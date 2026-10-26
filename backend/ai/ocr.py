"""Module K4a: OCR (text from a photo of a notice).

Uses Tesseract with Urdu + English ("urd+eng"). Runs on the server itself:
the image is never sent to an outside service, never stored, and the text is
never logged.

The upload must already have passed security.files.validate_upload() (file type,
size, EXIF stripped). This module adds its own limits on image size and OCR time.

Public contract (docs/api.md):
  extract_text(image_bytes: bytes) -> str
"""

from __future__ import annotations

import io
import os
import re
import shutil
from pathlib import Path

from PIL import Image, ImageOps

LANGS = os.getenv("HAQDAR_OCR_LANGS", "urd+eng")
TIMEOUT_SECONDS = 20
MAX_PIXELS = 25_000_000          # refuse giant images (decompression bombs)
MIN_WIDTH = 1500                 # small photos are upscaled: Tesseract reads better
WINDOWS_DEFAULT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


class OcrUnavailable(RuntimeError):
    """Tesseract is not installed or cannot be found."""


class OcrError(ValueError):
    """The image could not be read."""


def tesseract_path() -> str | None:
    """Find Tesseract: HAQDAR_TESSERACT_CMD, then PATH, then the Windows default."""
    configured = os.getenv("HAQDAR_TESSERACT_CMD")
    if configured and Path(configured).exists():
        return configured
    found = shutil.which("tesseract")
    if found:
        return found
    if WINDOWS_DEFAULT.exists():
        return str(WINDOWS_DEFAULT)
    return None


def is_available() -> bool:
    return tesseract_path() is not None


def preprocess(image: Image.Image) -> Image.Image:
    """Grayscale, fix rotation from the camera, boost contrast, upscale small photos."""
    image = ImageOps.exif_transpose(image)
    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image, cutoff=1)
    if image.width < MIN_WIDTH:
        scale = MIN_WIDTH / image.width
        image = image.resize((MIN_WIDTH, int(image.height * scale)), Image.LANCZOS)
    return image


def load_image(image_bytes: bytes) -> Image.Image:
    if not image_bytes:
        raise OcrError("empty image")
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.width * image.height > MAX_PIXELS:
            raise OcrError("image is too large")
        image.load()
    except OcrError:
        raise
    except Exception as exc:  # corrupt or unsupported file
        raise OcrError("could not read the image") from exc
    return image


def extract_text(image_bytes: bytes) -> str:
    """Return the text found in the image ("" if none)."""
    cmd = tesseract_path()
    if cmd is None:
        raise OcrUnavailable("Tesseract is not installed. Users can type or paste the notice instead.")

    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = cmd
    image = preprocess(load_image(image_bytes))
    try:
        # psm 6 = treat the image as one block of text (works well for notices)
        text = pytesseract.image_to_string(image, lang=LANGS, config="--psm 6", timeout=TIMEOUT_SECONDS)
    except RuntimeError as exc:  # pytesseract raises RuntimeError on timeout
        raise OcrError("reading the image took too long") from exc
    # Tesseract adds invisible direction marks around mixed Urdu/English runs; remove them.
    text = re.sub("[\u200e\u200f\u202a-\u202e\u2066-\u2069]", "", text)
    return "\n".join(line.rstrip() for line in text.splitlines() if line.strip())


if __name__ == "__main__":
    # Try it:  cd backend; python -m ai.ocr path\to\photo.jpg
    import sys

    if len(sys.argv) < 2:
        print("usage: python -m ai.ocr <image file>")
        sys.exit(1)
    print(extract_text(Path(sys.argv[1]).read_bytes()))

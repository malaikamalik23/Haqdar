import io

from PIL import Image

MAX_BYTES = 8 * 1024 * 1024
SIGNATURES = {b"\xff\xd8\xff": "jpeg", b"\x89PNG\r\n\x1a\n": "png", b"%PDF-": "pdf"}
Image.MAX_IMAGE_PIXELS = 40_000_000


class UploadError(ValueError):
    pass


def validate_upload(data: bytes, filename: str = "") -> bytes:
    """Validates an upload by its real bytes, not its extension.

    Returns cleaned bytes (images are re-encoded, which drops EXIF/GPS data).
    Everything stays in memory: nothing is written to disk.
    """
    if not data:
        raise UploadError("empty file")
    if len(data) > MAX_BYTES:
        raise UploadError("file too large")
    kind = next((k for sig, k in SIGNATURES.items() if data.startswith(sig)), None)
    if kind is None:
        raise UploadError("unsupported file type")
    if kind == "pdf":
        return data
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        raise UploadError("corrupt or unsafe image")
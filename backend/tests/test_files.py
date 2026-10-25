import io

import pytest
from PIL import Image

from security.files import MAX_BYTES, UploadError, validate_upload


def _jpeg_with_exif() -> bytes:
    img = Image.new("RGB", (10, 10), "white")
    exif = Image.Exif()
    exif[0x010F] = "FakeCamera"
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif.tobytes())
    return buf.getvalue()


def test_text_file_renamed_to_jpg_is_rejected():
    with pytest.raises(UploadError):
        validate_upload(b"hello world", "notice.jpg")


def test_empty_file_is_rejected():
    with pytest.raises(UploadError):
        validate_upload(b"", "a.png")


def test_oversized_file_is_rejected():
    with pytest.raises(UploadError):
        validate_upload(b"%PDF-" + b"0" * MAX_BYTES, "big.pdf")


def test_corrupt_image_is_rejected():
    with pytest.raises(UploadError):
        validate_upload(b"\xff\xd8\xff" + b"garbage", "a.jpg")


def test_exif_is_stripped():
    original = _jpeg_with_exif()
    assert len(Image.open(io.BytesIO(original)).getexif()) > 0
    cleaned = validate_upload(original, "photo.jpg")
    assert len(Image.open(io.BytesIO(cleaned)).getexif()) == 0


def test_pdf_passes_through():
    pdf = b"%PDF-1.4 fake but valid header"
    assert validate_upload(pdf, "notice.pdf") == pdf
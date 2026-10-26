"""Tests for Module K4a (OCR). The real-OCR test runs only where Tesseract is installed."""

import io

import pytest
from PIL import Image, ImageDraw, ImageFont

from ai import ocr


def png_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def text_image(lines, size=(1400, 420)):
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.load_default(size=44)
    except TypeError:  # older Pillow
        font = ImageFont.load_default()
    for i, line in enumerate(lines):
        draw.text((40, 40 + i * 80), line, fill="black", font=font)
    return image


def test_empty_bytes_rejected():
    with pytest.raises(ocr.OcrError):
        ocr.load_image(b"")


def test_corrupt_image_rejected():
    with pytest.raises(ocr.OcrError):
        ocr.load_image(b"not an image at all")


def test_giant_image_rejected(monkeypatch):
    monkeypatch.setattr(ocr, "MAX_PIXELS", 100)
    with pytest.raises(ocr.OcrError):
        ocr.load_image(png_bytes(Image.new("RGB", (50, 50), "white")))


def test_preprocess_grayscale_and_upscale():
    out = ocr.preprocess(Image.new("RGB", (500, 200), "white"))
    assert out.mode == "L" and out.width == ocr.MIN_WIDTH


def test_missing_tesseract_gives_clear_error(monkeypatch):
    monkeypatch.setattr(ocr, "tesseract_path", lambda: None)
    with pytest.raises(ocr.OcrUnavailable):
        ocr.extract_text(png_bytes(text_image(["hello"])))


@pytest.mark.skipif(not ocr.is_available(), reason="Tesseract is not installed here")
def test_real_ocr_reads_english_bill():
    image = text_image(["IESCO Electricity Bill", "Amount Payable: Rs 18,500", "Due Date: 20-11-2026"])
    text = ocr.extract_text(png_bytes(image))
    assert "IESCO" in text and "18,500" in text and "20-11-2026" in text

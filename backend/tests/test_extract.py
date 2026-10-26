import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

from main import Settings, create_app

CNIC = "35202-1234567-1"
PHONE = "0300-1234567"


def png(width=300, height=120, text=None):
    img = Image.new("RGB", (width, height), "white")
    if text:
        ImageDraw.Draw(img).text((20, 30), text, fill="black", font=ImageFont.load_default(size=44))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def post(client, data, name="notice.png", ctype="image/png", **kw):
    return client.post("/extract", files={"file": (name, data, ctype)}, **kw)


def client(**overrides):
    return TestClient(create_app(Settings(**overrides)))


@pytest.fixture
def fake_ocr(monkeypatch):
    """Real mode with the OCR step replaced, so no Tesseract is needed."""
    from ai import ocr

    state = {"text": f"Notice for CNIC {CNIC}. Call {PHONE}. Pay Rs 5000 by 30 November 2026."}
    monkeypatch.setattr(ocr, "extract_text", lambda image_bytes: state["text"])
    return state


# ---------- mock mode ----------

def test_mock_mode_returns_sample_text_without_needing_tesseract():
    r = post(client(ai_mode="mock"), png())
    assert r.status_code == 200
    d = r.json()
    assert "[REF_1]" in d["text"] and d["masked"] == 0 and d["truncated"] is False  # the sample already holds placeholders


# ---------- what comes back is masked ----------

def test_personal_numbers_are_masked_and_never_returned(fake_ocr):
    r = post(client(ai_mode="real"), png())
    assert r.status_code == 200
    d = r.json()
    assert CNIC not in r.text and PHONE not in r.text
    assert "[CNIC_1]" in d["text"] and "[PHONE_1]" in d["text"] and d["masked"] == 2
    assert "5000" in d["text"] and "30 November 2026" in d["text"]  # deadlines and amounts are kept
    assert set(d) == {"text", "masked", "truncated"}  # the mapping of real values is not part of the reply


def test_urdu_digit_phone_numbers_are_masked_too(fake_ocr):
    fake_ocr["text"] = "رابطہ کریں ۰۳۰۰-۱۲۳۴۵۶۷ پر"
    d = post(client(ai_mode="real"), png()).json()
    assert "۰۳۰۰" not in d["text"] and "[PHONE_1]" in d["text"]


def test_very_long_text_is_cut_to_the_limit(fake_ocr):
    fake_ocr["text"] = "word " * 3000
    d = post(client(ai_mode="real"), png()).json()
    assert len(d["text"]) == 4000 and d["truncated"] is True


# ---------- the upload itself is distrusted ----------

def test_a_pdf_that_is_not_really_a_pdf_gets_a_clean_error(fake_ocr):
    r = post(client(ai_mode="real"), b"%PDF-1.4 fake", "x.pdf", "application/pdf")
    assert r.status_code == 422 and r.json() == {"detail": "The PDF could not be read"}


def test_text_file_renamed_to_png_is_refused(fake_ocr):
    r = post(client(ai_mode="real"), b"just some text, not an image", "notice.png")
    assert r.status_code == 400 and r.json() == {"detail": "unsupported file type"}


def test_empty_and_corrupt_files_are_refused(fake_ocr):
    c = client(ai_mode="real")
    assert post(c, b"").status_code == 400
    assert post(c, b"\x89PNG\r\n\x1a\n" + b"garbage").status_code == 400


def test_phone_photos_keep_their_orientation_when_metadata_is_removed():
    from security.files import validate_upload

    stored = Image.new("RGB", (260, 1700), "white")  # a portrait photo, as the camera sensor stored it
    exif = Image.Exif()
    exif[0x0112] = 6  # "rotate 90 degrees clockwise to display"
    buf = io.BytesIO()
    stored.save(buf, format="JPEG", exif=exif.tobytes())
    cleaned = Image.open(io.BytesIO(validate_upload(buf.getvalue(), "phone.jpg")))
    assert cleaned.size == (1700, 260)
    assert len(cleaned.getexif()) == 0  # the metadata is still removed


def test_the_upload_limit_applies_with_and_without_a_declared_length(fake_ocr):
    c = client(ai_mode="real", upload_max_bytes=100_000)
    assert post(c, png()).status_code == 200
    big = png(2400, 2400)  # a plain white png is small, so pad it with data after the image
    padded = big + b"\x00" * 200_000
    assert post(c, padded).status_code == 413

    def chunks():
        for _ in range(300):  # 1.2 MB: over this route's cap of the upload limit plus 1 MB
            yield b"x" * 4000

    r = c.post("/extract", content=chunks(), headers={"content-type": "multipart/form-data; boundary=x"})
    assert r.status_code == 413


def test_other_routes_keep_the_small_body_limit(fake_ocr):
    c = client(ai_mode="real")
    r = c.post("/ask", json={"question": "x" * 70_000, "lang": "en"})
    assert r.status_code == 413
    assert post(c, png(1200, 1200) + b"\x00" * 100_000).status_code == 200  # /extract takes a larger body


def test_missing_file_field_is_a_clean_422(fake_ocr):
    r = client(ai_mode="real").post("/extract", data={"other": "x"})
    assert r.status_code == 422 and r.json()["detail"] == "Invalid request"


# ---------- errors do not leak and the route is protected ----------

def test_ocr_failures_return_generic_messages(monkeypatch):
    from ai import ocr

    c = client(ai_mode="real")

    def unavailable(_):
        raise ocr.OcrUnavailable("Tesseract is not installed at C:\\secret\\path")

    monkeypatch.setattr(ocr, "extract_text", unavailable)
    r = post(c, png())
    assert r.status_code == 503 and "secret" not in r.text

    def broken(_):
        raise ocr.OcrError("could not read the image: /tmp/abc.png")

    monkeypatch.setattr(ocr, "extract_text", broken)
    r = post(c, png())
    assert r.status_code == 422 and "abc.png" not in r.text

    monkeypatch.setattr(ocr, "extract_text", lambda _: "   \n  ")
    r = post(c, png())
    assert r.status_code == 422 and r.json() == {"detail": "No text was found in the photo"}


def test_extract_has_its_own_rate_limit(fake_ocr):
    c = client(ai_mode="mock", rate_extract_per_min=2)
    assert [post(c, png()).status_code for _ in range(2)] == [200, 200]
    r = post(c, png())
    assert r.status_code == 429 and int(r.headers["retry-after"]) >= 1
    assert c.post("/ask", json={"question": "my electricity meter is fast", "lang": "en"}).status_code == 200


def test_only_two_photos_are_read_at_once(fake_ocr, monkeypatch):
    import threading

    gate = threading.Event()
    from ai import ocr

    started = []

    def slow(_):
        started.append(1)
        gate.wait(5)
        return "Notice Rs 5000"

    monkeypatch.setattr(ocr, "extract_text", slow)
    c = client(ai_mode="real", rate_extract_per_min=50)
    results = []
    threads = [threading.Thread(target=lambda: results.append(post(c, png()).status_code)) for _ in range(2)]
    for t in threads:
        t.start()
    while len(started) < 2:
        pass
    assert post(c, png()).status_code == 503  # a third photo is told to wait
    gate.set()
    for t in threads:
        t.join()
    assert results == [200, 200]


def test_security_headers_are_on_upload_responses(fake_ocr):
    r = post(client(ai_mode="real"), png())
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["cache-control"] == "no-store"


# ---------- real Tesseract, where it is installed (CI installs it) ----------

def test_real_ocr_reads_an_english_notice_end_to_end():
    from ai import ocr

    if not ocr.is_available():
        pytest.skip("Tesseract is not installed")
    image = png(1600, 220, "Pay Rs 5000 by 30 November 2026")
    r = post(client(ai_mode="real"), image)
    assert r.status_code == 200, r.text
    assert "5000" in r.json()["text"]



def test_real_ocr_reads_a_rotated_phone_photo():
    from ai import ocr

    if not ocr.is_available():
        pytest.skip("Tesseract is not installed")
    upright = png(1700, 260, "Pay Rs 5000 by 30 November 2026")
    stored = Image.open(io.BytesIO(upright)).rotate(90, expand=True)  # how the sensor wrote it
    exif = Image.Exif()
    exif[0x0112] = 6
    buf = io.BytesIO()
    stored.save(buf, format="JPEG", exif=exif.tobytes())
    r = post(client(ai_mode="real"), buf.getvalue(), "phone.jpg", "image/jpeg")
    assert r.status_code == 200, r.text
    assert "5000" in r.json()["text"]

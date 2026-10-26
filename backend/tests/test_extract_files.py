import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from main import Settings, create_app

CNIC = "35202-1234567-1"
PHONE = "0300-1234567"


def make_pdf(pages):
    """A small text PDF built by hand, so the tests need no PDF-writing library."""
    n = len(pages)
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(n))
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", f"<< /Type /Pages /Kids [{kids}] /Count {n} >>"]
    for i, text in enumerate(pages):
        objs.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {4 + 2 * i} 0 R "
            f"/Resources << /Font << /F1 {3 + 2 * n} 0 R >> >> >>"
        )
        stream = f"BT /F1 14 Tf 50 700 Td ({text}) Tj ET"
        objs.append(f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream")
    objs.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    out, offsets = b"%PDF-1.4\n", []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def post(client, data, name="notice.pdf", ctype="application/pdf"):
    return client.post("/extract", files={"file": (name, data, ctype)})


def real_client(**overrides):
    return TestClient(create_app(Settings(ai_mode="real", **overrides)))


def test_a_pdf_with_text_is_read_and_masked():
    pdf = make_pdf([f"Notice for CNIC {CNIC}. Call {PHONE}. Pay Rs 5000 by 30 November 2026."])
    r = post(real_client(), pdf)
    assert r.status_code == 200
    d = r.json()
    assert CNIC not in r.text and PHONE not in r.text
    assert "[CNIC_1]" in d["text"] and "[PHONE_1]" in d["text"] and d["masked"] == 2
    assert "5000" in d["text"] and "30 November 2026" in d["text"]


def test_only_the_first_three_pages_are_read():
    pdf = make_pdf(["Page one", "Page two", "Page three", "Page four", "Page five MARKER"])
    text = post(real_client(), pdf).json()["text"]
    assert "Page one" in text and "Page three" in text
    assert "Page four" not in text and "MARKER" not in text


def test_pdf_text_is_cut_to_the_limit():
    d = post(real_client(), make_pdf(["word " * 800] * 3)).json()
    assert len(d["text"]) == 4000 and d["truncated"] is True


def test_a_scanned_pdf_gets_a_helpful_message():
    buf = io.BytesIO()
    Image.new("RGB", (400, 200), "white").save(buf, format="PDF")
    r = post(real_client(), buf.getvalue())
    assert r.status_code == 422
    assert "scan" in r.json()["detail"] and "photo" in r.json()["detail"]


def test_a_password_protected_pdf_is_refused():
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(200, 200)
    try:
        writer.encrypt("secret", algorithm="RC4-128")
    except Exception:
        pytest.skip("this pypdf version cannot write the test file")
    buf = io.BytesIO()
    writer.write(buf)
    r = post(real_client(), buf.getvalue())
    assert r.status_code == 422 and r.json() == {"detail": "The PDF is password protected"}


def test_a_broken_pdf_is_a_clean_422_that_does_not_repeat_the_file():
    r = post(real_client(), b"%PDF-1.4 this is not really a pdf, CNIC " + CNIC.encode())
    assert r.status_code == 422
    assert r.json() == {"detail": "The PDF could not be read"} and CNIC not in r.text


def test_a_pdf_over_the_upload_limit_is_refused():
    big = make_pdf(["x"]) + b"\x00" * 100_000
    assert post(real_client(upload_max_bytes=50_000), big).status_code == 413


def test_mock_mode_accepts_a_pdf():
    r = post(TestClient(create_app(Settings(ai_mode="mock"))), make_pdf(["anything"]))
    assert r.status_code == 200 and "[REF_1]" in r.json()["text"]

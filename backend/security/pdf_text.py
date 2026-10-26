"""Reads the text of a PDF, with hard limits, for /extract.

Only text that is already inside the PDF is read. Pages are never drawn, scripts and attachments
are never run or opened, and a scanned PDF (pictures of pages) is reported as "no text".
"""
import io

MAX_PAGES = 3  # a notice is rarely longer, and it bounds the work done for one upload
MAX_CHARS = 20_000  # text collected before masking and shortening


class PdfError(ValueError):
    """The PDF could not be read."""


class PdfUnavailable(PdfError):
    """The PDF library is not installed on this server."""


class PdfEncrypted(PdfError):
    """The PDF is password protected."""


class PdfNoText(PdfError):
    """The PDF has no text inside (for example a scan)."""


def extract_pdf_text(data: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        raise PdfUnavailable("pypdf is not installed") from None
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise PdfEncrypted("password protected")
        parts, total = [], 0
        for index in range(min(len(reader.pages), MAX_PAGES)):
            page_text = reader.pages[index].extract_text() or ""
            parts.append(page_text)
            total += len(page_text)
            if total >= MAX_CHARS:
                break
    except PdfError:
        raise
    except Exception:
        raise PdfError("the PDF could not be read") from None
    text = "\n".join(parts).strip()[:MAX_CHARS]
    if not text:
        raise PdfNoText("no text in the PDF")
    return text

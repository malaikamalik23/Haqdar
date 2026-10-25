"""Module K6: Letter generator.

Fills a Jinja2 template for a pack with the user's details, in Urdu or English.

Privacy rules:
  - The letter is built locally. Nothing is sent to an external service.
  - This module NEVER logs or stores the fields it receives (they contain personal data).
Safety:
  - Only known fields are used; unknown fields are ignored.
  - Values are cleaned (control characters and template syntax removed, length limited).
  - Missing fields become a visible placeholder like [name], so the user can fill them in.

Public contract (docs/api.md):
  render_letter(pack_id: str, fields: dict, lang: str = "ur") -> str
  letter_fields(pack_id: str) -> list[str]     (for the web app's form)
  letter_html(pack_id, fields, lang) -> str     (printable page, right-to-left for Urdu)
"""

from __future__ import annotations

import datetime as _dt
import html
import re
from pathlib import Path

from jinja2 import FileSystemLoader, StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates" / "letters"
LANGS = ("ur", "en")
MAX_FIELD_CHARS = 500

# Fields each letter uses. "date" is filled automatically if not given.
LETTER_FIELDS = {
    "electricity_bill_dispute": ["name", "address", "reference_no", "bill_month", "amount",
                                 "reason", "disco", "subdivision", "date"],
    "fbr_tax_notice": ["name", "address", "notice_no", "notice_date", "tax_year",
                       "reply_summary", "tax_office", "date"],
}

_env = SandboxedEnvironment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    undefined=StrictUndefined,
    autoescape=False,          # plain text; the web app sanitises output before display
    keep_trailing_newline=True,
)

RLM = "\u200f"  # invisible right-to-left mark: keeps mixed Urdu/English lines in the right order

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TEMPLATE_SYNTAX = re.compile(r"\{[{%#]|[}%#]\}")


class LetterError(ValueError):
    pass


def letter_fields(pack_id: str) -> list[str]:
    if pack_id not in LETTER_FIELDS:
        raise LetterError(f"no letter template for pack '{pack_id}'")
    return list(LETTER_FIELDS[pack_id])


def clean_value(value) -> str:
    """Make a user value safe to put in a letter."""
    text = _CONTROL.sub("", str(value))
    text = _TEMPLATE_SYNTAX.sub("", text)
    return text.strip()[:MAX_FIELD_CHARS]


def render_letter(pack_id: str, fields: dict, lang: str = "ur") -> str:
    allowed = letter_fields(pack_id)
    lang = lang if lang in LANGS else "ur"
    fields = fields or {}

    values = {}
    for key in allowed:
        raw = fields.get(key)
        value = clean_value(raw) if raw not in (None, "") else ""
        values[key] = value or f"[{key}]"
    if values["date"] == "[date]":
        values["date"] = _dt.date.today().strftime("%d-%m-%Y")

    template = _env.get_template(f"{pack_id}.{lang}.j2")
    text = template.render(**values)
    if lang == "ur":
        text = "\n".join(RLM + line if line.strip() else line for line in text.split("\n"))
    return text


def letter_html(pack_id: str, fields: dict, lang: str = "ur") -> str:
    """A clean, printable HTML page of the letter (right-to-left for Urdu).

    All user values are HTML-escaped, so nothing in a field can run as code."""
    lang = lang if lang in LANGS else "ur"
    text = render_letter(pack_id, fields, lang).replace(RLM, "")
    direction = "rtl" if lang == "ur" else "ltr"
    font = "'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', serif" if lang == "ur" else "Georgia, serif"
    line_height = "2.4" if lang == "ur" else "1.7"
    body = html.escape(text)
    return f"""<!doctype html>
<html lang="{lang}" dir="{direction}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Haqdar letter</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap">
<style>
  body {{ background:#eef1f4; margin:0; padding:32px 16px; }}
  .page {{ max-width:720px; margin:0 auto; background:#fff; padding:48px 56px;
          border-radius:8px; box-shadow:0 2px 12px rgba(0,0,0,.08); }}
  .letter {{ white-space:pre-wrap; font-family:{font}; font-size:18px; line-height:{line_height};
            color:#1d2733; text-align:start; unicode-bidi:plaintext; }}
  @media print {{ body {{ background:#fff; padding:0; }} .page {{ box-shadow:none; }} }}
</style>
</head>
<body><div class="page"><div class="letter">{body}</div></div></body>
</html>
"""


if __name__ == "__main__":
    # Try it:  cd backend; python -m ai.letters          (text in the terminal)
    #          cd backend; python -m ai.letters --html   (right-to-left preview in the browser)
    import sys

    sample_ur = {"name": "علی خان", "address": "مکان نمبر 1، گلی نمبر 2، اسلام آباد", "reference_no": "00 00000 0000000",
                 "bill_month": "اکتوبر 2026", "amount": "18,500", "reason": "یونٹس میرے عام استعمال سے تین گنا زیادہ ہیں۔",
                 "disco": "آئیسکو (IESCO)", "subdivision": "جی-9 سب ڈویژن"}
    sample_en = {"name": "Ali Khan", "address": "House 1, Street 2, Islamabad", "reference_no": "00 00000 0000000",
                 "bill_month": "October 2026", "amount": "18,500", "reason": "The units are three times my usual use.",
                 "disco": "IESCO", "subdivision": "G-9 Sub-Division"}
    if "--html" in sys.argv:
        # Opens a right-to-left preview of the Urdu letter in your browser.
        import tempfile
        import webbrowser

        for lang, sample in (("ur", sample_ur), ("en", sample_en)):
            path = Path(tempfile.gettempdir()) / f"haqdar_letter_{lang}.html"
            path.write_text(letter_html("electricity_bill_dispute", sample, lang), encoding="utf-8")
            webbrowser.open(path.as_uri())
            print(f"Opened {path}")
    else:
        print(render_letter("electricity_bill_dispute", sample_ur, "ur"))
        print("-" * 60)
        print(render_letter("electricity_bill_dispute", sample_en, "en"))

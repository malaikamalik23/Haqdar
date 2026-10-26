"""Module K4b: Key-field extraction from notice text.

Finds sender, date, deadline, amount and demand in English, Roman Urdu or Urdu
notice text (typed, pasted, or from OCR). Rule-based and explainable: every field
comes from a visible pattern in the text. Missing fields are returned as "".

Public contract (docs/api.md):
  extract_fields(text: str) -> {sender, date, deadline, amount, demand}
"""

from __future__ import annotations

import re

MAX_CHARS = 8000

# Known senders: (pattern, display name). Checked in order.
SENDERS = [
    (r"\bIESCO\b|آئیسکو", "IESCO"), (r"\bLESCO\b|لیسکو", "LESCO"), (r"\bMEPCO\b|میپکو", "MEPCO"),
    (r"\bFESCO\b|فیسکو", "FESCO"), (r"\bGEPCO\b|گیپکو", "GEPCO"), (r"\bPESCO\b|پیسکو", "PESCO"),
    (r"\bHESCO\b", "HESCO"), (r"\bSEPCO\b", "SEPCO"), (r"\bQESCO\b", "QESCO"), (r"\bTESCO\b", "TESCO"),
    (r"\bK-?Electric\b", "K-Electric"), (r"\bNEPRA\b|نیپرا", "NEPRA"),
    (r"\bFBR\b|Federal Board of Revenue|ایف بی آر", "FBR"),
    (r"Inland Revenue|Commissioner", "FBR (Inland Revenue)"),
    (r"\bNADRA\b|نادرا", "NADRA"), (r"\bSNGPL\b", "SNGPL"), (r"\bSSGC\b", "SSGC"),
    (r"Rent Controller|رینٹ کنٹرولر", "Rent Controller"),
]

MONTHS = ("january|february|march|april|may|june|july|august|september|october|november|december|"
          "jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec")
URDU_MONTHS = "جنوری|فروری|مارچ|اپریل|مئی|جون|جولائی|اگست|ستمبر|اکتوبر|نومبر|دسمبر"

DATE_RE = re.compile(
    rf"\b\d{{4}}[-/.]\d{{1,2}}[-/.]\d{{1,2}}\b"                         # 2026-11-20 (ISO, or RTL-reversed by OCR)
    rf"|\b\d{{1,2}}[-/.]\d{{1,2}}[-/.]\d{{2,4}}\b"                      # 20-11-2026, 20/11/26
    rf"|\b\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTHS})[a-z]*,?\s+\d{{4}}\b"   # 20 November 2026
    rf"|\b(?:{MONTHS})[a-z]*\s+\d{{1,2}},?\s+\d{{4}}\b"                   # November 20, 2026
    rf"|\d{{1,2}}\s+(?:{URDU_MONTHS})\s+\d{{4}}",                          # 20 نومبر 2026
    re.IGNORECASE,
)
DEADLINE_HINT = re.compile(
    r"due date|last date|pay by|payable by|before|not later than|deadline|within|by\s*$|"
    r"aakhri tareekh|akhri tareekh|tak\b|آخری|سے پہلے|تک",
    re.IGNORECASE,
)
ISSUE_HINT = re.compile(r"issue date|issued on|dated|date of issue|bill date|\bdate\b|تاریخ اجرا|مورخہ", re.IGNORECASE)
AMOUNT_RE = re.compile(
    r"(?:Rs\.?|PKR|روپے)\s*[:\-]?\s*([\d,]+(?:\.\d{1,2})?)"
    r"|([\d,]+(?:\.\d{1,2})?)\s*(?:/-|rupees|rupay|روپے)",
    re.IGNORECASE,
)
AMOUNT_HINT = re.compile(r"payable|amount|total|due|demand|ادا|رقم|واجب", re.IGNORECASE)
DEMAND_HINT = re.compile(
    r"\b(pay|deposit|submit|file|furnish|appear|reply|respond|provide|vacate|send)\b|"
    r"\b(ada|jama|bhej|pesh)\b|ادا|جمع|حاضر|جواب|پیش|بھیج",
    re.IGNORECASE,
)
# Money-style number with thousands separators (18,500), used when OCR loses the currency word.
MONEY_SHAPE = re.compile(r"(?<![\d-])\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?(?![\d-])")
_ISO_DATE = re.compile(r"^(\d{4})([-/.])(\d{1,2})\2(\d{1,2})$")
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?۔])\s+|\n+")


def _clean(text: str) -> str:
    return (text or "")[:MAX_CHARS]


def find_sender(text: str) -> str:
    for pattern, name in SENDERS:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    m = re.search(r"^\s*(?:from|sender)\s*[:\-]\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip()[:80] if m else ""


def _dates_with_context(text: str):
    """Yield (date_string, text_before_it_on_the_same_line, text_after_it)."""
    for m in DATE_RE.finditer(text):
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        line_end = len(text) if line_end == -1 else line_end
        yield normalize_date(m.group(0).strip()), text[max(line_start, m.start() - 40):m.start()], text[m.end():min(line_end, m.end() + 15)]


def normalize_date(date: str) -> str:
    """Year-first dates (2026-11-20) become day-first (20-11-2026), like the rest of Pakistan's notices.

    Right-to-left Urdu text often comes out of OCR with the date reversed this way."""
    m = _ISO_DATE.match(date)
    return f"{m.group(4)}{m.group(2)}{m.group(3)}{m.group(2)}{m.group(1)}" if m else date


def find_dates(text: str) -> tuple[str, str]:
    """Return (issue_date, deadline). A date near a deadline word is the deadline."""
    issue, deadline = "", ""
    for date, before, after in _dates_with_context(text):
        if not deadline and (DEADLINE_HINT.search(before) or re.match(r"\s*(tak|تک|سے پہلے)", after)):
            deadline = date
        elif not issue and (ISSUE_HINT.search(before) or not deadline):
            issue = date
    return issue, deadline


def find_amount(text: str) -> str:
    """Prefer an amount on a line that says payable/amount/total/due."""
    best = ""
    for line in text.splitlines() or [text]:
        for m in AMOUNT_RE.finditer(line):
            value = (m.group(1) or m.group(2) or "").strip(",")
            if not value or not re.search(r"\d", value):
                continue
            if AMOUNT_HINT.search(line):
                return value
            best = best or value
    if best:
        return best
    m = MONEY_SHAPE.search(text)
    return m.group(0) if m else ""


def find_demand(text: str) -> str:
    """The first sentence that asks the reader to do something."""
    for sentence in _SENTENCE_SPLIT.split(text):
        s = sentence.strip()
        if len(s) > 8 and DEMAND_HINT.search(s):
            return s[:200]
    return ""


def extract_fields(text: str) -> dict:
    text = _clean(text)
    issue, deadline = find_dates(text)
    return {
        "sender": find_sender(text),
        "date": issue,
        "deadline": deadline,
        "amount": find_amount(text),
        "demand": find_demand(text),
    }


if __name__ == "__main__":
    # Try it:  cd backend; python -m ai.extract
    import json

    sample = """IESCO - Islamabad Electric Supply Company
Bill Date: 05-11-2026
Amount Payable: Rs 18,500
Due Date: 20-11-2026
Please pay the amount before the due date to avoid a late payment surcharge."""
    print(json.dumps(extract_fields(sample), ensure_ascii=False, indent=2))

import re

PATTERNS = [
    ("IBAN",  re.compile(r"\bPK\d{2}[A-Z]{4}\d{16}\b")),
    ("EMAIL", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("CNIC",  re.compile(r"\b\d{5}-?\d{7}-?\d\b")),
    ("PHONE", re.compile(r"(?<!\d)(?:\+92|0092|[0۰٠])[-\s]?[3۳٣]\d{2}[-\s]?\d{7}(?!\d)")),  # also Urdu and Arabic-Indic digits
]

# Reference-type numbers are redacted only when a label comes right before them,
# and only if the value contains at least one digit.
LABELLED = re.compile(
    r"(?i)\b((?:reference|ref|consumer|customer|account|meter|challan|ntn)"
    r"\s*(?:no\.?|number|#|id)?\s*[:\-]?\s*)"
    r"((?=[A-Z0-9\-/]*\d)[A-Z0-9][A-Z0-9\-/]{5,})"
)


def redact(text: str):
    """Returns (redacted_text, mapping of placeholder -> original value).

    The mapping holds the real identifiers. Keep it in memory only: never log it,
    never store it, never send it to an external service.
    """
    mapping, seen, counters = {}, {}, {}

    def placeholder(label, val):
        if val in seen:
            return seen[val]
        counters[label] = counters.get(label, 0) + 1
        ph = f"[{label}_{counters[label]}]"
        seen[val], mapping[ph] = ph, val
        return ph

    for label, pat in PATTERNS:
        text = pat.sub(lambda m, label=label: placeholder(label, m.group(0)), text)
    text = LABELLED.sub(lambda m: m.group(1) + placeholder("REF", m.group(2)), text)
    return text, mapping
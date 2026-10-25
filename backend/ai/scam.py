"""Module K5: Scam-language score.

Detects pressure tactics typical of fake notices: urgency, threats, payment
pressure, requests for secret codes, and prize bait. Works for English,
Roman Urdu and Urdu.

Score = rules + (1 - rules) * MODEL_BOOST * classifier     (0..1)
  The classifier can only RAISE the rule score, never pull clear rule evidence down.
  - Rules: explainable signals. Each matched category adds weight; several
    categories together push the score up fast.
  - Classifier: TF-IDF character n-grams + logistic regression, trained on a
    SMALL synthetic labelled set (backend/ai/data/scam_examples.yaml).

This is ONE signal for the fake-notice verdict (security.notice_check flags >= 0.7),
not a final judgement. Real official notices can also mention penalties or
disconnection, which is why a single category stays below 0.7.

Public contract (docs/api.md):
  score_language(text: str) -> {score: float, signals: [str]}
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

DATA_FILE = Path(__file__).resolve().parent / "data" / "scam_examples.yaml"
MODEL_BOOST = 0.5
MAX_CHARS = 5000

# category -> (weight, human-readable reason, patterns in en / roman / ur)
CATEGORIES = {
    "urgency": (0.35, "Pressure to act immediately", [
        r"\burgent(ly)?\b", r"\bimmediately\b", r"\bact now\b", r"\blast chance\b", r"\bfinal warning\b",
        r"\bwithin \d+ ?(hours?|hrs?|minutes?)\b", r"\btoday only\b|\bonly today\b",
        r"\bfor[ai]n\b", r"\bfori\b", r"\bjaldi\b", r"\babhi\b", r"\baakhri warning\b", r"\b\d+ ?ghant[ey]\b",
        r"فوری", r"فوراً", r"جلدی", r"آخری وارننگ", r"ابھی", r"گھنٹے میں",
    ]),
    "threat": (0.35, "Threat of arrest, legal action, blocking or disconnection", [
        r"\barrest", r"\bpolice\b", r"\blegal (action|case)\b", r"\bcase will be filed\b", r"\bblock(ed)?\b",
        r"\bsuspend(ed)?\b", r"\bblacklist", r"\bwill be (cut|disconnected)\b",
        r"\bkaat di\b", r"\bkaat\b", r"\bband ho\b", r"\bkarwai\b", r"\bcase darj\b", r"\bwarna\b",
        r"گرفتار", r"پولیس", r"کارروائی", r"مقدمہ", r"کاٹ دی", r"بند ہو", r"ورنہ",
    ]),
    "payment_pressure": (0.35, "Asks for money through an unusual channel or to a person", [
        r"\beasy ?paisa\b", r"\bjazz ?cash\b", r"\bsadapay\b", r"\bnayapay\b", r"\bgift ?card\b",
        r"\bwestern union\b", r"\bpay the agent\b", r"\bsend (money|payment)\b",
        r"\bpaise bhej", r"\brupay .*bhej", r"ایزی پیسہ", r"جاز کیش", r"رقم بھیج",
    ]),
    "secret_request": (0.6, "Asks for a PIN, OTP, password or card number", [
        r"\botp\b", r"\bpin\b", r"\bpin code\b", r"\bpassword\b", r"\bverification code\b", r"\bcard number\b",
        r"\bcvv\b", r"\bcode (bhej|reply)", r"\bcode\b.*\bbhej", r"پن کوڈ", r"پاس ورڈ", r"کوڈ بھیج",
    ]),
    "prize_bait": (0.5, "Promises a prize, lottery or unexpected refund", [
        r"\bcongratulations\b", r"\byou (have )?won\b", r"\bprize\b", r"\blottery\b", r"\brefund available\b",
        r"\bmubarak ho\b", r"\binaam\b", r"مبارک ہو", r"انعام", r"لاٹری",
    ]),
}
_COMPILED = {name: [re.compile(p, re.IGNORECASE) for p in pats] for name, (_, _, pats) in CATEGORIES.items()}


def rule_signals(text: str) -> list[tuple[str, str]]:
    """Return (category, matched_text) for each category found in the text."""
    found = []
    for name, patterns in _COMPILED.items():
        for pat in patterns:
            m = pat.search(text)
            if m:
                found.append((name, m.group(0)))
                break
    return found


def rule_score(categories: list[str]) -> float:
    """Combine category weights: 1 - product(1 - w). One category stays modest."""
    remaining = 1.0
    for name in categories:
        remaining *= 1.0 - CATEGORIES[name][0]
    return 1.0 - remaining


@lru_cache(maxsize=1)
def _model():
    """Train the small classifier once (takes well under a second)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline

    rows = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
    texts = [r["text"] for r in rows]
    labels = [r["label"] for r in rows]
    model = make_pipeline(
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), lowercase=True, sublinear_tf=True),
        LogisticRegression(max_iter=1000, C=2.0),
    )
    model.fit(texts, labels)
    return model


def model_score(text: str) -> float:
    return float(_model().predict_proba([text])[0][1])


def score_language(text: str) -> dict:
    text = (text or "")[:MAX_CHARS]
    if not text.strip():
        return {"score": 0.0, "signals": []}
    found = rule_signals(text)
    rules = rule_score([c for c, _ in found])
    model = model_score(text)
    score = rules + (1.0 - rules) * MODEL_BOOST * model
    signals = [f"{CATEGORIES[c][1]} (\"{m}\")" for c, m in found]
    return {"score": round(min(1.0, score), 4), "signals": signals}


if __name__ == "__main__":
    # Try it:  cd backend; python -m ai.scam "fori 5000 easypaisa karein warna bijli kaat di jayegi"
    import json
    import sys

    print(json.dumps(score_language(" ".join(sys.argv[1:])), ensure_ascii=False, indent=2))

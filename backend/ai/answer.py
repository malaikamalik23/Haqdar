"""Module K3: Grounded answer generator.

Builds the answer ONLY from retrieved pack steps, so every step is backed by an
official source. If the evidence is weak, it abstains ("cannot verify") instead
of guessing.

Pipeline:
  question -> retrieval.search() -> pick best pack -> keep that pack's strong steps
  -> citation check (step text + source must exist in the pack) -> answer or abstain

Privacy: this mode sends nothing outside the server. Retrieval runs locally.
(An optional LLM summary, if added later, must use security.redact + security.payload.)

Public contract (docs/api.md):
  answer_question(question: str, lang: str) ->
    {answer_ur, steps[{text_ur, source_id}], sources[{id, url, quote}], confidence, abstained}
    + answer_en and text_en on each step when lang == "en"
"""

from __future__ import annotations

import os
import re

from . import pack_loader, retrieval

# Below this top score we abstain. First check: in-scope 0.35-0.39, out-of-scope 0.07-0.10.
# Re-tune with the evaluation set (K7).
ABSTAIN_THRESHOLD = float(os.getenv("HAQDAR_ABSTAIN_THRESHOLD", "0.25"))
# A step is kept if its score is at least this fraction of the best score.
RELATIVE_KEEP = 0.75
TOP_K = 6
MAX_QUESTION_CHARS = 1000
LANGS = ("ur", "en")

ABSTAIN_UR = (
    "معذرت، ہم اس سوال کا جواب اپنے تصدیق شدہ سرکاری ذرائع سے نہیں دے سکتے۔ "
    "اندازہ لگانے کے بجائے ہم آپ کو مشورہ دیتے ہیں کہ متعلقہ سرکاری دفتر سے براہِ راست رابطہ کریں۔"
)
ABSTAIN_EN = (
    "Sorry, we cannot answer this from our verified official sources. "
    "Instead of guessing, we recommend contacting the relevant government office directly."
)

_packs_cache: dict | None = None

# English inside Urdu text, e.g. "(Electric Inspector / POI)", gets jumbled in right-to-left
# layout. Wrapping each bracketed English part in a left-to-right isolate keeps it in one piece.
LRI, PDI = "\u2066", "\u2069"
_LATIN_IN_BRACKETS = re.compile(r"\([^()]*[A-Za-z][^()]*\)")


NBSP = "\u00a0"  # non-breaking space: keeps "(Electric Inspector / POI)" on one line


def isolate_english(text: str) -> str:
    return _LATIN_IN_BRACKETS.sub(lambda m: f"{LRI}{m.group(0).replace(' ', NBSP)}{PDI}", text)


def _get_packs() -> dict:
    global _packs_cache
    if _packs_cache is None:
        _packs_cache = {p["id"]: p for p in pack_loader.load_all_packs()}
    return _packs_cache


def _abstain(lang: str, confidence: float, available: list[dict]) -> dict:
    out = {
        "answer_ur": ABSTAIN_UR,
        "steps": [],
        "sources": [],
        "confidence": round(confidence, 4),
        "abstained": True,
        "available_procedures": available,
    }
    if lang == "en":
        out["answer_en"] = ABSTAIN_EN
    return out


def citation_check(steps: list[dict], pack: dict) -> list[dict]:
    """Drop any step whose text or source is not exactly in the pack.

    In extractive mode this should never drop anything; it is a safety net for
    future changes (e.g. an LLM rewriting steps)."""
    pack_steps = {(s["text_ur"], s["source_id"]) for s in pack["steps"]}
    source_ids = {s["id"] for s in pack["sources"]}
    return [
        s for s in steps
        if (s.get("text_ur"), s.get("source_id")) in pack_steps and s.get("source_id") in source_ids
    ]


def answer_question(question: str, lang: str = "ur", *, retriever=None, packs=None,
                    threshold: float | None = None) -> dict:
    lang = lang if lang in LANGS else "ur"
    packs = packs if packs is not None else _get_packs()
    threshold = ABSTAIN_THRESHOLD if threshold is None else threshold
    available = [{"id": p["id"], "title_ur": p["title_ur"], "title_en": p["title_en"]} for p in packs.values()]

    question = (question or "").strip()[:MAX_QUESTION_CHARS]
    if not question:
        return _abstain(lang, 0.0, available)

    results = (retriever.search(question, TOP_K) if retriever is not None
               else retrieval.search(question, TOP_K))
    if not results or results[0]["score"] < threshold:
        return _abstain(lang, results[0]["score"] if results else 0.0, available)

    best = results[0]
    pack = packs.get(best["pack_id"])
    if pack is None:
        return _abstain(lang, best["score"], available)

    # Keep strong steps from the best pack, shown in the pack's own order.
    keep_ids = {r["step_id"] for r in results
                if r["pack_id"] == pack["id"] and r["score"] >= best["score"] * RELATIVE_KEEP}
    steps = []
    for s in pack["steps"]:
        if s["id"] in keep_ids:
            step = {"text_ur": s["text_ur"], "source_id": s["source_id"]}
            if lang == "en":
                step["text_en"] = s["text_en"]
            steps.append(step)

    steps = citation_check(steps, pack)
    if not steps:
        return _abstain(lang, best["score"], available)

    used = {s["source_id"] for s in steps}
    sources = [
        {"id": src["id"], "url": src["url"], "quote": src["quote"], **({"title": src["title"]} if "title" in src else {})}
        for src in pack["sources"] if src["id"] in used
    ]

    out = {
        "answer_ur": isolate_english(
            f"یہ معلومات «{pack['title_ur']}» کے سرکاری ذرائع سے لی گئی ہیں۔ نیچے دیے گئے اقدامات پر عمل کریں۔ متعلقہ دفتر: {pack['office']}"),
        "steps": steps,
        "sources": sources,
        "confidence": round(best["score"], 4),
        "abstained": False,
        "pack_id": pack["id"],
        "documents_needed": pack.get("documents_needed", []),
    }
    if lang == "en":
        out["answer_en"] = (f"This information comes from official sources for \"{pack['title_en']}\". "
                            f"Follow the steps below.")
    return out


if __name__ == "__main__":
    # Try it:  cd backend; python -m ai.answer "meter tez chal raha hai"
    import json
    import sys

    q = " ".join(sys.argv[1:]) or "میرا بل بہت زیادہ آیا ہے"
    print(json.dumps(answer_question(q, "en"), ensure_ascii=False, indent=2))

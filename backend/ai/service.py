"""API-facing functions: what each Haqdar endpoint returns (owner: Malaika Khan).

backend/main.py (the FastAPI app) calls these, so the web layer stays thin and all AI
logic lives in backend/ai/. Everything runs on the server: no external AI service is
called, and nothing here logs or stores user text.

  procedures()                  -> GET  /procedures
  ask(question, lang)           -> POST /ask
  analyze(text, lang)           -> POST /analyze   (typed or pasted notice text)
  analyze_image(bytes, lang)    -> for a future photo upload endpoint (OCR first)
  letter(pack_id, fields, lang) -> POST /letter
"""

from __future__ import annotations

from security.notice_check import check_notice

from . import answer, extract, letters, pack_loader, scam


class NotFound(LookupError):
    """Unknown pack id (the API turns this into 404)."""


def procedures() -> list[dict]:
    return [{"id": p["id"], "title_ur": p["title_ur"], "title_en": p["title_en"]}
            for p in pack_loader.load_all_packs()]


def ask(question: str, lang: str = "ur", *, retriever=None) -> dict:
    return answer.answer_question(question, lang, retriever=retriever)


def _explanation_ur(f_ur: dict, ans: dict) -> str:
    # The facts (sender, amount, deadline) are returned separately in fields / fields_ur and
    # the web app shows them under "Notice details", so the explanation is just the answer.
    return ans["answer_ur"]


def _explanation_en(fields: dict, ans: dict) -> str:
    return ans.get("answer_en", "")


def analyze(text: str, lang: str = "ur", *, retriever=None) -> dict:
    """Explain a notice: key facts, scam check, and the steps from the matching pack."""
    text = (text or "").strip()
    fields = extract.extract_fields(text)
    f_ur = extract.fields_ur(fields)
    language = scam.score_language(text)
    verdict = check_notice(text, [], language["score"])
    if verdict["label"] == "suspicious":
        # Show the exact pressure tactics found, not just "urgent or threatening language".
        verdict = {**verdict, "reasons": list(dict.fromkeys(verdict["reasons"] + language["signals"]))}

    ans = answer.answer_question(text, lang, retriever=retriever) if text else answer.answer_question("", lang)
    out = {
        "fields": fields,
        "fields_ur": f_ur,
        "explanation_ur": _explanation_ur(f_ur, ans),
        "steps": ans["steps"],
        "sources": ans["sources"],
        "verdict": verdict,
        "scam": language,
        "abstained": ans["abstained"],
    }
    if "pack_id" in ans:
        out["pack_id"] = ans["pack_id"]
    if lang == "en":
        out["explanation_en"] = _explanation_en(fields, ans)
    return out


def analyze_image(image_bytes: bytes, lang: str = "ur", *, retriever=None) -> dict:
    """OCR a validated image, then analyze the text. The caller must run
    security.files.validate_upload() first. The OCR text is returned so the user can check it."""
    from . import ocr

    text = ocr.extract_text(image_bytes)
    return {**analyze(text, lang, retriever=retriever), "ocr_text": text}


def letter(pack_id: str, fields: dict, lang: str = "ur") -> dict:
    try:
        return {"letter_text": letters.render_letter(pack_id, fields, lang)}
    except letters.LetterError as exc:
        raise NotFound(str(exc)) from exc

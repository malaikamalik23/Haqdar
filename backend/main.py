from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Haqdar API (mock)")

SOURCES = [{"id": "demo-src", "url": "https://example.gov.pk", "quote": "demo excerpt"}]
STEPS = [
    {
        "text_ur": "پہلا قدم: بل کی کاپی اور میٹر ریڈنگ جمع کریں۔",
        "text_en": "Step 1: Submit a copy of the bill and the meter reading.",
        "source_id": "demo-src",
    }
]

Lang = Literal["ur", "en"]


class AskRequest(BaseModel):
    question: str
    lang: Lang = "ur"


class AnalyzeRequest(BaseModel):
    text: str = ""
    lang: Lang = "ur"


class LetterRequest(BaseModel):
    pack_id: str
    fields: dict = {}
    lang: Lang = "ur"


@app.get("/procedures")
def procedures():
    return [
        {
            "id": "electricity-bill-dispute",
            "title_ur": "بجلی کے بل پر اعتراض",
            "title_en": "Disputing an electricity bill",
        }
    ]


@app.post("/ask")
def ask(req: AskRequest):
    return {
        "answer_ur": "یہ نمونہ جواب ہے۔",
        "answer_en": "This is a sample answer.",
        "steps": STEPS,
        "sources": SOURCES,
        "confidence": 0.9,
        "abstained": False,
    }


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return {
        "fields": {"sender": "Demo Dept", "date": "", "deadline": "", "amount": "", "demand": ""},
        "explanation_ur": "یہ نمونہ وضاحت ہے۔",
        "explanation_en": "This is a sample explanation.",
        "steps": STEPS,
        "sources": SOURCES,
        "verdict": {"label": "unclear", "reasons": ["mock response"]},
        "abstained": False,
    }


@app.post("/letter")
def letter(req: LetterRequest):
    if req.lang == "en":
        return {"letter_text": "Sample letter"}
    return {"letter_text": "نمونہ خط"}
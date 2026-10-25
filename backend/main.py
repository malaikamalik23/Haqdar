from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Haqdar API (mock)")

SOURCES = [{"id": "demo-src", "url": "https://example.gov.pk", "quote": "demo excerpt"}]
STEPS = [{"text_ur": "پہلا قدم: بل کی کاپی اور میٹر ریڈنگ جمع کریں۔", "source_id": "demo-src"}]

class AskRequest(BaseModel):
    question: str
    lang: str = "ur"

class AnalyzeRequest(BaseModel):
    text: str = ""

class LetterRequest(BaseModel):
    pack_id: str
    fields: dict = {}

@app.get("/procedures")
def procedures():
    return [{"id": "electricity-bill-dispute", "title_ur": "بجلی کے بل پر اعتراض"}]

@app.post("/ask")
def ask(req: AskRequest):
    return {"answer_ur": "یہ نمونہ جواب ہے۔", "steps": STEPS,
            "sources": SOURCES, "confidence": 0.9, "abstained": False}

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    return {"fields": {"sender": "Demo Dept", "date": "", "deadline": "", "amount": "", "demand": ""},
            "explanation_ur": "یہ نمونہ وضاحت ہے۔", "steps": STEPS, "sources": SOURCES,
            "verdict": {"label": "unclear", "reasons": ["mock response"]}, "abstained": False}

@app.post("/letter")
def letter(req: LetterRequest):
    return {"letter_text": "نمونہ خط"}
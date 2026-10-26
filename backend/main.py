import os
from dataclasses import dataclass
from typing import Literal

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from security.http_guard import BodySizeLimitMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware

DEV_ORIGINS = ("http://localhost:5500", "http://127.0.0.1:5500")
MAX_TEXT_CHARS = 4000  # matches the limit in the web app


def _env_int(name, default):
    try:
        return max(1, int(os.environ.get(name, default)))
    except ValueError:
        return default


def _env_flag(name):
    return os.environ.get(name, "0").strip().lower() in ("1", "true", "yes")


@dataclass(frozen=True)
class Settings:
    allowed_origins: tuple = DEV_ORIGINS
    max_body_bytes: int = 64 * 1024
    rate_write_per_min: int = 20
    rate_read_per_min: int = 60
    trust_proxy: bool = False
    docs_enabled: bool = True
    hsts: bool = False
    # "real" uses the AI modules in backend/ai. "mock" returns fixed sample answers: fast,
    # needs no AI model, and is what tests and early front-end work use. Settings() made
    # directly in code defaults to mock; the running server (from_env) defaults to real.
    ai_mode: str = "mock"

    @classmethod
    def from_env(cls):
        """Reads HAQDAR_* environment variables. Defaults are safe for local development."""
        origins = tuple(o.strip() for o in os.environ.get("HAQDAR_ALLOWED_ORIGINS", "").split(",") if o.strip())
        production = os.environ.get("HAQDAR_ENV", "development").strip().lower() == "production"
        return cls(
            allowed_origins=origins or DEV_ORIGINS,
            max_body_bytes=_env_int("HAQDAR_MAX_BODY_BYTES", 64 * 1024),
            rate_write_per_min=_env_int("HAQDAR_RATE_WRITE", 20),
            rate_read_per_min=_env_int("HAQDAR_RATE_READ", 60),
            trust_proxy=_env_flag("HAQDAR_TRUST_PROXY"),
            docs_enabled=not production,
            hsts=_env_flag("HAQDAR_HSTS"),
            ai_mode="mock" if os.environ.get("HAQDAR_AI_MODE", "real").strip().lower() == "mock" else "real",
        )


Lang = Literal["ur", "en"]


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)
    lang: Lang = "ur"


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(default="", max_length=MAX_TEXT_CHARS)
    lang: Lang = "ur"


class LetterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    pack_id: str = Field(pattern=r"^[a-z0-9_-]{1,64}$")
    fields: dict[str, str] = Field(default_factory=dict)
    lang: Lang = "ur"

    @field_validator("fields")
    @classmethod
    def small_fields(cls, value):
        if len(value) > 20 or any(len(k) > 40 or len(v) > 300 for k, v in value.items()):
            raise ValueError("too many or too long fields")
        return value


SOURCES = [{"id": "demo-src", "url": "https://example.gov.pk", "quote": "demo excerpt"}]
STEPS = [
    {
        "text_ur": "پہلا قدم: بل کی کاپی اور میٹر ریڈنگ جمع کریں۔",
        "text_en": "Step 1: Submit a copy of the bill and the meter reading.",
        "source_id": "demo-src",
    }
]


def create_app(settings=None):
    s = settings or Settings.from_env()
    app = FastAPI(
        title="Haqdar API" if s.ai_mode == "real" else "Haqdar API (mock)",
        docs_url="/docs" if s.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if s.docs_enabled else None,
    )

    # add_middleware puts the last one added on the outside, so the order below means:
    # security headers -> CORS -> rate limit -> body size limit -> the app.
    # Headers and CORS wrap the guards, so 413 and 429 responses carry them too.
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=s.max_body_bytes)
    app.add_middleware(RateLimitMiddleware, write_limit=s.rate_write_per_min,
                       read_limit=s.rate_read_per_min, trust_proxy=s.trust_proxy)
    app.add_middleware(CORSMiddleware, allow_origins=list(s.allowed_origins),
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"], max_age=600)
    app.add_middleware(SecurityHeadersMiddleware, hsts=s.hsts)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        # The default 422 body repeats the rejected input. Here only the field name and the
        # kind of problem are returned, so personal text never comes back in an error.
        errors = [{"field": ".".join(str(p) for p in e["loc"][1:]) or "body", "problem": e["type"]}
                  for e in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": "Invalid request", "errors": errors})

    @app.get("/health")
    def health():
        return {"status": "ok"}

    real = s.ai_mode == "real"

    def service():
        # Imported on first use, so importing main.py (tests, mock mode) needs no AI libraries.
        from ai import service as svc
        return svc

    @app.get("/procedures")
    def procedures():
        if real:
            return service().procedures()
        return [
            {
                "id": "electricity-bill-dispute",
                "title_ur": "بجلی کے بل پر اعتراض",
                "title_en": "Disputing an electricity bill",
            }
        ]

    @app.post("/ask")
    def ask(req: AskRequest):
        if real:
            return service().ask(req.question, req.lang)
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
        if real:
            return service().analyze(req.text, req.lang)
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
        if real:
            try:
                return service().letter(req.pack_id, req.fields, req.lang)
            except LookupError:  # ai.service.NotFound
                return JSONResponse(status_code=404, content={"detail": "Unknown procedure"})
        if req.lang == "en":
            return {"letter_text": "Sample letter"}
        return {"letter_text": "نمونہ خط"}

    return app


app = create_app()
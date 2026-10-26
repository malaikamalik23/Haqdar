import os
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal

from fastapi import FastAPI, File, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from security.files import UploadError, validate_upload
from security.http_guard import BodySizeLimitMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware
from security.redact import redact

DEV_ORIGINS = ("http://localhost:5500", "http://127.0.0.1:5500")
MAX_TEXT_CHARS = 4000  # matches the limit in the web app
MOCK_PHOTO_TEXT = (
    "FBR Notice: an amount of Rs 5000 is outstanding. Consumer No: [REF_1]. "
    "Pay by 30 November 2026 using Easypaisa, or call [PHONE_1]."
)  # what /extract returns in mock mode


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
    upload_max_bytes: int = 8 * 1024 * 1024  # largest photo /extract accepts
    rate_extract_per_min: int = 6  # reading a photo is expensive, so it has its own limit
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
            upload_max_bytes=_env_int("HAQDAR_UPLOAD_MAX_BYTES", 8 * 1024 * 1024),
            rate_extract_per_min=_env_int("HAQDAR_RATE_EXTRACT", 6),
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
    real = s.ai_mode == "real"

    @asynccontextmanager
    async def lifespan(app):
        if real:
            # Load the search model now, so the first question is fast and a broken install
            # fails when the server starts, not when someone asks a question.
            from ai import retrieval

            retrieval.get_retriever()
        yield

    app = FastAPI(
        lifespan=lifespan,
        title="Haqdar API" if s.ai_mode == "real" else "Haqdar API (mock)",
        docs_url="/docs" if s.docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if s.docs_enabled else None,
    )

    # add_middleware puts the last one added on the outside, so the order below means:
    # security headers -> CORS -> rate limit -> body size limit -> the app.
    # Headers and CORS wrap the guards, so 413 and 429 responses carry them too.
    # Only /extract (photo upload) gets a bigger body limit and its own, stricter rate limit.
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=s.max_body_bytes,
                       path_max_bytes={"/extract": s.upload_max_bytes + 1024 * 1024})
    app.add_middleware(RateLimitMiddleware, write_limit=s.rate_write_per_min,
                       read_limit=s.rate_read_per_min, trust_proxy=s.trust_proxy,
                       path_limits={"/extract": s.rate_extract_per_min})
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

    ocr_slots = threading.BoundedSemaphore(2)  # at most two photos are read at the same time

    @app.post("/extract")
    async def extract(file: UploadFile = File(...)):
        """Reads the text from a photo of a notice.

        The photo is checked, read in memory and never kept. Personal details are masked in the
        reply, and the user reviews the text before sending it to /analyze.
        """
        data = await file.read(s.upload_max_bytes + 1)
        if len(data) > s.upload_max_bytes:
            return JSONResponse(status_code=413, content={"detail": "file too large"})
        try:
            cleaned = validate_upload(data, "")
        except UploadError as exc:
            status = 413 if str(exc) == "file too large" else 400
            return JSONResponse(status_code=status, content={"detail": str(exc)})
        if cleaned.startswith(b"%PDF-"):
            return JSONResponse(status_code=415, content={"detail": "Please send a JPG or PNG photo"})

        if not real:
            text = MOCK_PHOTO_TEXT
        else:
            from ai import ocr

            if not ocr_slots.acquire(blocking=False):
                return JSONResponse(status_code=503, content={"detail": "Busy, try again in a moment"},
                                    headers={"Retry-After": "5"})
            try:
                text = await run_in_threadpool(ocr.extract_text, cleaned)
            except ocr.OcrUnavailable:
                return JSONResponse(status_code=503, content={"detail": "Reading photos is not available on this server"})
            except ocr.OcrError:
                return JSONResponse(status_code=422, content={"detail": "The photo could not be read"})
            finally:
                ocr_slots.release()

        masked, found = redact(text)  # the mapping of real values is never returned or kept
        truncated = len(masked) > MAX_TEXT_CHARS
        masked = masked[:MAX_TEXT_CHARS]
        if not masked.strip():
            return JSONResponse(status_code=422, content={"detail": "No text was found in the photo"})
        return {"text": masked, "masked": len(found), "truncated": truncated}

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
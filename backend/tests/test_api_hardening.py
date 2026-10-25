import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from main import Settings, create_app
from security.http_guard import RateLimitMiddleware

OK_BODY = {"question": "bill is too high", "lang": "en"}


def client(**overrides):
    return TestClient(create_app(Settings(**overrides)))


# ---------- security headers ----------

def test_security_headers_on_every_response():
    r = client().get("/health")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert r.headers["referrer-policy"] == "no-referrer"
    assert "microphone=()" in r.headers["permissions-policy"]
    assert r.headers["cache-control"] == "no-store"
    assert "default-src 'none'" in r.headers["content-security-policy"]


def test_docs_page_is_exempt_from_the_strict_csp_but_keeps_other_headers():
    r = client(docs_enabled=True).get("/docs")
    assert r.status_code == 200
    assert "content-security-policy" not in r.headers
    assert r.headers["x-content-type-options"] == "nosniff"


def test_docs_are_off_in_production():
    c = client(docs_enabled=False)
    assert c.get("/docs").status_code == 404
    assert c.get("/openapi.json").status_code == 404


def test_hsts_only_when_enabled():
    assert "strict-transport-security" not in client().get("/health").headers
    assert "max-age" in client(hsts=True).get("/health").headers["strict-transport-security"]


def test_error_responses_also_carry_security_headers():
    r = client(max_body_bytes=100).post("/ask", json={"question": "x" * 500, "lang": "en"})
    assert r.status_code == 413
    assert r.headers["x-content-type-options"] == "nosniff"


# ---------- body size ----------

def test_oversized_body_with_content_length_is_rejected():
    r = client(max_body_bytes=200).post("/ask", json={"question": "x" * 1000, "lang": "en"})
    assert r.status_code == 413
    assert r.json() == {"detail": "Request body too large"}


def test_oversized_streamed_body_without_content_length_is_rejected():
    def chunks():
        for _ in range(50):
            yield b"x" * 100

    r = client(max_body_bytes=1000).post("/ask", content=chunks(), headers={"content-type": "application/json"})
    assert r.status_code == 413


def test_normal_body_is_accepted():
    assert client().post("/ask", json=OK_BODY).status_code == 200


# ---------- rate limiting ----------

def test_write_requests_are_rate_limited_with_retry_after():
    c = client(rate_write_per_min=3)
    assert [c.post("/ask", json=OK_BODY).status_code for _ in range(3)] == [200, 200, 200]
    r = c.post("/ask", json=OK_BODY)
    assert r.status_code == 429
    assert int(r.headers["retry-after"]) >= 1


def test_reads_and_writes_are_counted_separately():
    c = client(rate_write_per_min=1, rate_read_per_min=5)
    assert c.post("/ask", json=OK_BODY).status_code == 200
    assert c.post("/ask", json=OK_BODY).status_code == 429
    assert c.get("/procedures").status_code == 200


def test_spoofed_forwarded_for_header_does_not_bypass_the_limit():
    c = client(rate_write_per_min=2, trust_proxy=False)
    codes = [c.post("/ask", json=OK_BODY, headers={"x-forwarded-for": f"10.0.0.{i}"}).status_code for i in range(4)]
    assert codes == [200, 200, 429, 429]


def test_trusted_proxy_separates_clients_by_forwarded_for():
    c = client(rate_write_per_min=1, trust_proxy=True)
    assert c.post("/ask", json=OK_BODY, headers={"x-forwarded-for": "9.9.9.1"}).status_code == 200
    assert c.post("/ask", json=OK_BODY, headers={"x-forwarded-for": "9.9.9.2"}).status_code == 200
    assert c.post("/ask", json=OK_BODY, headers={"x-forwarded-for": "9.9.9.1"}).status_code == 429


def test_limit_resets_after_the_window():
    now = [0.0]
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, write_limit=1, read_limit=1, window=60, clock=lambda: now[0])

    @app.get("/ping")
    def ping():
        return {"ok": True}

    c = TestClient(app)
    assert c.get("/ping").status_code == 200
    assert c.get("/ping").status_code == 429
    now[0] = 61.0
    assert c.get("/ping").status_code == 200


def test_rate_limit_memory_is_bounded():
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, write_limit=5, read_limit=5, trust_proxy=True, max_clients=3)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    c = TestClient(app)
    for i in range(10):
        c.get("/ping", headers={"x-forwarded-for": f"1.1.1.{i}"})
    layer = app.middleware_stack
    while layer is not None and not isinstance(layer, RateLimitMiddleware):
        layer = getattr(layer, "app", None)
    assert layer is not None and len(layer.hits) <= 3


# ---------- CORS ----------

def test_allowed_origin_gets_cors_header_and_others_do_not():
    c = client()
    ok = c.get("/health", headers={"origin": "http://localhost:5500"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:5500"
    bad = c.get("/health", headers={"origin": "https://evil.example"})
    assert "access-control-allow-origin" not in bad.headers


def test_preflight_from_allowed_origin_succeeds():
    r = client().options("/ask", headers={
        "origin": "http://localhost:5500",
        "access-control-request-method": "POST",
        "access-control-request-headers": "content-type",
    })
    assert r.status_code == 200
    assert "POST" in r.headers["access-control-allow-methods"]


def test_rate_limit_responses_are_readable_by_the_web_app():
    c = client(rate_write_per_min=1)
    c.post("/ask", json=OK_BODY, headers={"origin": "http://localhost:5500"})
    r = c.post("/ask", json=OK_BODY, headers={"origin": "http://localhost:5500"})
    assert r.status_code == 429
    assert r.headers["access-control-allow-origin"] == "http://localhost:5500"


def test_origins_come_from_the_environment(monkeypatch):
    monkeypatch.setenv("HAQDAR_ALLOWED_ORIGINS", "https://haqdar.example, https://www.haqdar.example")
    monkeypatch.setenv("HAQDAR_ENV", "production")
    s = Settings.from_env()
    assert s.allowed_origins == ("https://haqdar.example", "https://www.haqdar.example")
    assert s.docs_enabled is False


def test_bad_numbers_in_the_environment_fall_back_to_defaults(monkeypatch):
    monkeypatch.setenv("HAQDAR_RATE_WRITE", "lots")
    assert Settings.from_env().rate_write_per_min == 20


# ---------- input validation and privacy ----------

def test_validation_errors_never_echo_the_input():
    r = client().post("/ask", json={"question": "my CNIC is 35202-1234567-1", "lang": "xx"})
    assert r.status_code == 422
    assert "35202" not in r.text and "CNIC" not in r.text
    assert r.json()["detail"] == "Invalid request"
    assert {"field": "lang", "problem": "literal_error"} in r.json()["errors"]


def test_question_length_is_limited():
    assert client().post("/ask", json={"question": "x" * 4001, "lang": "en"}).status_code == 422
    assert client().post("/ask", json={"question": "", "lang": "en"}).status_code == 422


def test_unknown_fields_are_rejected():
    assert client().post("/ask", json={**OK_BODY, "admin": True}).status_code == 422


def test_letter_request_limits():
    c = client()
    good = {"pack_id": "electricity-bill-dispute", "fields": {"name": "A"}, "lang": "en"}
    assert c.post("/letter", json=good).status_code == 200
    assert c.post("/letter", json={**good, "pack_id": "fbr_tax_notice"}).status_code == 200
    assert c.post("/letter", json={**good, "pack_id": "../etc/passwd"}).status_code == 422
    assert c.post("/letter", json={**good, "fields": {f"k{i}": "v" for i in range(21)}}).status_code == 422
    assert c.post("/letter", json={**good, "fields": {"name": "x" * 301}}).status_code == 422


def test_mock_endpoints_still_return_the_documented_shapes():
    c = client()
    ask = c.post("/ask", json=OK_BODY).json()
    assert {"answer_ur", "answer_en", "steps", "sources", "confidence", "abstained"} <= ask.keys()
    ana = c.post("/analyze", json={"text": "notice", "lang": "ur"}).json()
    assert {"fields", "explanation_ur", "explanation_en", "verdict", "abstained"} <= ana.keys()
    assert c.get("/procedures").json()[0]["id"] == "electricity-bill-dispute"
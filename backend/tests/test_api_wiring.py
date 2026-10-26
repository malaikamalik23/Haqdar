"""The API in real mode returns answers from the AI modules (backend/ai).

Uses a tiny fake embedder, so no AI model is downloaded. Skipped where the AI
libraries are not installed (e.g. a minimal environment with only requirements.txt).
"""
import pytest

pytest.importorskip("faiss")
pytest.importorskip("numpy")

from fastapi.testclient import TestClient  # noqa: E402

from ai import retrieval  # noqa: E402
from main import Settings, create_app  # noqa: E402


class FakeEmbedder:
    dim = 64

    def encode(self, texts):
        import numpy as np
        out = np.zeros((len(texts), self.dim), dtype="float32")
        for i, t in enumerate(texts):
            for tok in retrieval.tokenize(t):
                out[i, sum(map(ord, tok)) % self.dim] += 1.0
        return out


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(retrieval, "_default_retriever", retrieval.build_retriever(embedder=FakeEmbedder()))
    return TestClient(create_app(Settings(ai_mode="real", rate_write_per_min=1000, rate_read_per_min=1000)))


def test_procedures_lists_the_real_packs(client):
    ids = {p["id"] for p in client.get("/procedures").json()}
    assert {"electricity_bill_dispute", "fbr_tax_notice", "cnic_renewal", "rent_islamabad"} <= ids


def test_ask_returns_grounded_steps_with_real_sources(client):
    data = client.post("/ask", json={"question": "meter tez chal raha hai check", "lang": "en"}).json()
    assert data["abstained"] is False and data["steps"]
    returned = {s["id"] for s in data["sources"]}
    assert all(step["source_id"] in returned for step in data["steps"])
    assert all("example" not in s["url"] for s in data["sources"])  # not the mock source
    assert "answer_en" in data


class NoMeaningEmbedder:
    """Every text gets the same vector, so only keywords can match."""

    def encode(self, texts):
        import numpy as np
        out = np.zeros((len(texts), 8), dtype="float32")
        out[:, 0] = 1.0
        return out


def test_ask_out_of_scope_abstains(monkeypatch):
    monkeypatch.setattr(retrieval, "_default_retriever", retrieval.build_retriever(embedder=NoMeaningEmbedder()))
    monkeypatch.setattr(retrieval, "SEMANTIC_WEIGHT", 0.0)
    client = TestClient(create_app(Settings(ai_mode="real")))
    data = client.post("/ask", json={"question": "write me a poem about cricket", "lang": "ur"}).json()
    assert data["abstained"] is True and data["steps"] == []


def test_analyze_scam_message_is_suspicious_with_reasons(client):
    text = "fori 5000 rupay jazzcash par bhejein warna aaj bijli kaat di jayegi"
    data = client.post("/analyze", json={"text": text, "lang": "ur"}).json()
    assert data["verdict"]["label"] == "suspicious"
    assert any("JazzCash" in r or "jazzcash" in r for r in data["verdict"]["reasons"])
    assert data["scam"]["score"] >= 0.7


def test_analyze_bill_extracts_fields_and_urdu_display(client):
    text = "IESCO\nBill Date: 05-11-2026\nAmount Payable: Rs 18,500\nDue Date: 20-11-2026\nPlease pay the bill."
    data = client.post("/analyze", json={"text": text, "lang": "en"}).json()
    assert data["fields"]["amount"] == "18,500" and data["fields"]["deadline"] == "20-11-2026"
    assert "نومبر" in data["fields_ur"]["deadline_ur"]
    assert "explanation_en" in data


def test_letter_is_real_and_unknown_pack_is_404(client):
    ok = client.post("/letter", json={"pack_id": "electricity_bill_dispute", "fields": {"name": "Ali"}, "lang": "en"})
    assert ok.status_code == 200 and "Ali" in ok.json()["letter_text"]
    missing = client.post("/letter", json={"pack_id": "no_such_pack", "fields": {}, "lang": "en"})
    assert missing.status_code == 404


def test_settings_from_env_default_to_real_and_mock_can_be_chosen(monkeypatch):
    monkeypatch.delenv("HAQDAR_AI_MODE", raising=False)
    assert Settings.from_env().ai_mode == "real"
    monkeypatch.setenv("HAQDAR_AI_MODE", "mock")
    assert Settings.from_env().ai_mode == "mock"

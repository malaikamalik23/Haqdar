from fastapi.testclient import TestClient

from main import Settings, create_app


def test_real_mode_loads_the_search_model_when_the_server_starts(monkeypatch):
    calls = []
    from ai import retrieval

    monkeypatch.setattr(retrieval, "get_retriever", lambda: calls.append("loaded"))
    with TestClient(create_app(Settings(ai_mode="real"))):
        assert calls == ["loaded"]


def test_mock_mode_loads_nothing_at_start(monkeypatch):
    calls = []
    from ai import retrieval

    monkeypatch.setattr(retrieval, "get_retriever", lambda: calls.append("loaded"))
    with TestClient(create_app(Settings(ai_mode="mock"))) as c:
        assert c.get("/health").status_code == 200
    assert calls == []

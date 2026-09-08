import app.main as main
from fastapi.testclient import TestClient

client = TestClient(main.app)


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


async def _fake_allowed(tenant_id, tokens):
    return True, 42


async def _fake_denied(tenant_id, tokens):
    return False, 0


async def _fake_complete_primary(payload):
    return _FakeResponse({"id": "primary-1"}), "primary"


async def _fake_complete_unavailable(payload):
    return None, "primary_error"


def _headers():
    return {"Authorization": "Bearer tenant1"}


def _body():
    return {"messages": [{"role": "user", "content": "hi"}], "max_tokens": 10}


def test_successful_completion_returns_200(monkeypatch):
    monkeypatch.setattr(main.limiter, "try_consume", _fake_allowed)
    monkeypatch.setattr(main.router, "complete", _fake_complete_primary)
    resp = client.post("/v1/chat/completions", headers=_headers(), json=_body())
    assert resp.status_code == 200
    assert resp.json() == {"id": "primary-1"}
    assert resp.headers["X-Model-Provider"] == "primary"


def test_rate_limit_exceeded_returns_429(monkeypatch):
    monkeypatch.setattr(main.limiter, "try_consume", _fake_denied)
    resp = client.post("/v1/chat/completions", headers=_headers(), json=_body())
    assert resp.status_code == 429
    assert resp.json()["error"]["code"] == "rate_limit_exceeded"
    assert resp.headers["Retry-After"] == "60"


def test_model_unavailable_returns_503(monkeypatch):
    monkeypatch.setattr(main.limiter, "try_consume", _fake_allowed)
    monkeypatch.setattr(main.router, "complete", _fake_complete_unavailable)
    resp = client.post("/v1/chat/completions", headers=_headers(), json=_body())
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "model_unavailable"


def test_missing_auth_returns_401():
    resp = client.post("/v1/chat/completions", json=_body())
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_api_key"


def test_invalid_body_returns_400():
    resp = client.post("/v1/chat/completions", headers=_headers(), content=b"not json")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_request"

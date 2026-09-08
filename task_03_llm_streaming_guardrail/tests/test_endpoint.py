import app.main as main
from app.stream_buffer import StreamingRedactor
from fastapi.testclient import TestClient

client = TestClient(main.app)


async def _fake_stream_provider(payload, url):
    # Exercises the same StreamingRedactor the real stream_provider uses, so this
    # test covers the full main.py -> StreamingResponse -> client wire path with
    # real redaction, just without the httpx call to a live upstream.
    redactor = StreamingRedactor()
    for chunk in ("Hello, my email is ", "alice@example.com done"):
        safe = redactor.feed(chunk)
        if safe:
            yield safe
    tail = redactor.flush()
    if tail:
        yield tail


def test_completion_endpoint_streams_redacted_text(monkeypatch):
    monkeypatch.setattr(main, "stream_provider", _fake_stream_provider)
    resp = client.post("/v1/chat/completions", json={"model": "x", "messages": []})
    assert resp.status_code == 200
    assert "[REDACTED]" in resp.text
    assert "alice@example.com" not in resp.text


def test_malformed_body_returns_400_not_500():
    resp = client.post("/v1/chat/completions", content=b"not json")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_request"

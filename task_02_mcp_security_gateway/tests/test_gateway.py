import app.gateway as gateway
from fastapi.testclient import TestClient

client = TestClient(gateway.app)


async def _fake_forward(payload, url):
    if payload.get("method") == "tools/list":
        return 200, {"jsonrpc": "2.0", "id": payload.get("id"),
                      "result": {"tools": [{"name": "get_customer_record"}, {"name": "admin_reset_key"}]}}
    return 200, {"jsonrpc": "2.0", "id": payload.get("id"),
                  "result": {"content": [{"type": "text", "text": "executed"}]}}


def test_viewer_tools_list_is_forwarded(monkeypatch):
    monkeypatch.setattr(gateway, "forward", _fake_forward)
    resp = client.post("/mcp", headers={"Authorization": "Bearer viewer-token"},
                        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert resp.status_code == 200
    assert resp.json()["result"]["tools"][0]["name"] == "get_customer_record"


def test_viewer_calling_admin_tool_is_blocked(monkeypatch):
    monkeypatch.setattr(gateway, "forward", _fake_forward)
    resp = client.post("/mcp", headers={"Authorization": "Bearer viewer-token"},
                        json={"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                              "params": {"name": "admin_reset_key"}})
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"]["code"] == -32001


def test_admin_calling_admin_tool_is_forwarded(monkeypatch):
    monkeypatch.setattr(gateway, "forward", _fake_forward)
    resp = client.post("/mcp", headers={"Authorization": "Bearer admin-token"},
                        json={"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                              "params": {"name": "admin_reset_key"}})
    assert resp.status_code == 200
    assert resp.json()["result"]["content"][0]["text"] == "executed"


def test_missing_auth_header_returns_error(monkeypatch):
    monkeypatch.setattr(gateway, "forward", _fake_forward)
    resp = client.post("/mcp", json={"jsonrpc": "2.0", "id": 4, "method": "tools/list"})
    assert resp.status_code == 200
    assert resp.json()["error"]["code"] == -32000

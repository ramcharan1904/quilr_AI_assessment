# Task 2 — MCP Security Gateway

A FastAPI reverse proxy that sits in front of an MCP server and adds auth + authorization
to the `/mcp` JSON-RPC endpoint, without touching the downstream server itself.

```
client --Bearer token--> gateway (:8000) --> downstream MCP server (:9000)
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
# terminal 1 — the (mock) downstream MCP server
uvicorn mock_server.server:app --port 9000

# terminal 2 — the gateway
uvicorn app.gateway:app --port 8000
```

```bash
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"admin_reset_key"}}'
```

## Test

```bash
pytest
```

## How it works

- **`app/auth.py`** — `authenticate()` reads the `Authorization: Bearer <token>` header
  against a static token→role map (`admin-token` → `admin`, `viewer-token` → `viewer`).
  Missing/malformed/unknown tokens fail closed with JSON-RPC error `-32000`.
- **`app/authorization.py`** — `authorized(role, method, params)` only gates the
  `tools/call` method: tool names prefixed `admin_` require the `admin` role, everything
  else is allowed. All other JSON-RPC methods (`tools/list`, `initialize`, `ping`, …) pass
  through untouched — the gateway restricts tool *execution*, not protocol introspection.
  A denied call returns JSON-RPC error `-32001` ("Unauthorized Tool Call").
- **`app/proxy.py`** — forwards the authorized request to `DOWNSTREAM_MCP_URL`
  (env var, default `http://127.0.0.1:9000/mcp`) and relays the response as-is.
- **`mock_server/`** — a stand-in downstream MCP server (two tools: `get_customer_record`,
  `admin_reset_key`) used for local testing and in the test suite; not part of the graded
  gateway logic itself.

## Design notes

- Auth/authorization failures are returned as **HTTP 200 with a JSON-RPC `error` object**,
  matching how MCP clients expect errors on this transport, rather than HTTP 401/403.
- Tokens and roles are hardcoded for the assessment; a real deployment would swap
  `TOKENS` in `app/auth.py` for a proper identity provider / token introspection call.

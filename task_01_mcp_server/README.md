# Task 1 — Custom MCP Server

A minimal [MCP](https://modelcontextprotocol.io/) server (built on `FastMCP`, stdio transport)
exposing two tools backed by an in-memory customer store:

| Tool | Input | Behavior |
|---|---|---|
| `get_customer_record` | `customer_id: "CUST-#####"` | Returns the matching record, or `{"status": "not_found"}` |
| `trigger_refund` | `customer_id`, `amount > 0`, `reason` (≥10 chars) | Returns a `refund_accepted` acknowledgement |

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python -m app.server
```

Starts the server on stdio — it's meant to be spawned by an MCP client, not hit directly.
See `examples/demo_client.py` for a client that spawns it, lists tools, and calls both
valid and invalid arguments:

```bash
python examples\demo_client.py
```

## Test

```bash
pytest
```

`tests/test_validation.py` covers the pydantic schemas directly; `tests/test_protocol.py`
drives the server over a real stdio `ClientSession` and asserts on JSON-RPC error codes.

## Design notes

- **Validation happens twice, on purpose.** `app/tools.py` re-validates with pydantic even
  though FastMCP already validates against the generated JSON schema — the tool functions
  need to be safe to call directly (e.g. from tests) without relying on the transport layer.
- **The tricky part: real JSON-RPC errors, not `isError: true`.** FastMCP's own tool
  dispatch swallows every exception and folds it into a "successful" `CallToolResult` with
  `isError=True` — there's no way to make a validated tool raise a genuine top-level
  JSON-RPC error from inside that path. To satisfy "reject invalid formats with standard
  MCP JSON-RPC error codes," `app/server.py` installs a custom `CallToolRequest` handler
  that validates arguments *before* handing off to FastMCP, raising `McpError` (→ real
  `INVALID_PARAMS` / `METHOD_NOT_FOUND` JSON-RPC errors) instead of a masked tool result.
  See the comment in `app/server.py` for the full mechanics.

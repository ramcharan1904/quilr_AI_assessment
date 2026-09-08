# Task 1 — Custom MCP Server
Install: `pip install -r requirements.txt`
Run: `python -m app.server`
Test: `pytest tests/`

STDOUT is reserved for MCP/JSON-RPC traffic. Logs go to STDERR.

Invalid tool arguments (bad `customer_id` format, non-positive `amount`, short
`reason`) and unknown tool names return real top-level JSON-RPC errors
(`-32602 Invalid params` / `-32601 Method not found`), not a masked
`isError: true` tool result. This requires a small custom `CallToolRequest`
handler in `server.py` — FastMCP's default tool dispatch swallows every
exception from a tool into `isError: true`, so validation runs before
handing off to it. See `tests/test_protocol.py` for live coverage against a
real stdio session.

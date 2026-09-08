# Task 2 — MCP Security Gateway
Run:
`uvicorn app.gateway:app --port 8000`

Tokens:
- `admin-token` => admin
- `viewer-token` => viewer

viewer may call `tools/list`, but cannot call `admin_*`.

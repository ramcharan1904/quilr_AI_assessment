# FDE Assessment — Complete Code

Four supplied tasks, each independently runnable (own `requirements.txt`, own tests). See
each task's README for setup, run instructions, and design notes.

| Task | Description |
|---|---|
| [`task_01_mcp_server`](task_01_mcp_server/README.md) | Custom MCP server (stdio) exposing two tools, with real JSON-RPC error codes on invalid input |
| [`task_02_mcp_security_gateway`](task_02_mcp_security_gateway/README.md) | Auth + role-based authorization proxy in front of an MCP server |
| [`task_03_llm_streaming_guardrail`](task_03_llm_streaming_guardrail/README.md) | Streaming proxy that redacts PII from an LLM response in real time, including PII split across chunks |
| [`task_04_llm_rate_limit_fallback`](task_04_llm_rate_limit_fallback/README.md) | SQLite-backed per-tenant token rate limiter with automatic failover to a secondary provider |

## Quick start

Each task is self-contained — `cd` into it, create a venv, `pip install -r requirements.txt`,
then follow that task's README for run/test commands. There's no shared root-level
environment or dependency set.

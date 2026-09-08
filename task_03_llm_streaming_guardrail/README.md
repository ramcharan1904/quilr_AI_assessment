# Task 3 — Streaming PII Guardrail
Run: `uvicorn app.main:app --port 8001`

The proxy maintains a small rolling buffer so PII split across chunks can be detected.

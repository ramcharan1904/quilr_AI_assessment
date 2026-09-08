# Task 3 — Streaming PII Guardrail

A FastAPI proxy that sits between a client and a streaming LLM provider, redacting PII
(emails, SSNs, credit card numbers) from the response **as it streams**, including PII
whose characters are split across separate SSE chunks.

```
client <--redacted text-- guardrail (:8001) <--SSE deltas-- upstream LLM (:9100)
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
# terminal 1 — a stand-in upstream that streams PII split across small deltas
uvicorn examples.mock_upstream:app --port 9100

# terminal 2 — the guardrail
uvicorn app.main:app --port 8001
```

```bash
curl -N -X POST http://127.0.0.1:8001/v1/chat/completions \
  -H "Content-Type: application/json" -d '{"messages":[{"role":"user","content":"hi"}]}'
```

Watch the output arrive as it streams — the email/card/SSN in `examples/mock_upstream.py`
come out as `[REDACTED]` even though the mock deliberately chunks the text into
6-character pieces to simulate token-by-token delivery.

## Test

```bash
pytest
```

`tests/test_pii.py` covers the regexes directly, `tests/test_stream_buffer.py` covers
buffering/boundary logic in isolation, `tests/test_endpoint.py` drives the full endpoint.

## How it works

- **`app/pii_detector.py`** — regex matchers for email, SSN, and credit card numbers
  (card matches are additionally checked with a Luhn checksum to cut false positives on
  plain 13–19 digit runs). `find_match_spans()` returns match positions without mutating
  the text, so the buffer can reason about *where* a match is without relying on
  substitution-shortened output.
- **`app/stream_buffer.py`** (`StreamingRedactor`) — the core problem this task is
  actually about: a naive per-chunk regex would miss PII that's split across two
  `feed()` calls (e.g. `"alice@exam"` + `"ple.com"`). Instead, `feed()` keeps a rolling
  tail of the last `MAX_PATTERN_LENGTH` characters (64 — long enough for any SSN/card
  match, and a practical cutoff for emails) unreleased, and only emits text up to a
  boundary that isn't in the middle of a potential match. `flush()` redacts and releases
  whatever's left once the stream ends.
- **`app/stream_proxy.py`** — parses upstream SSE (`data: {...}` lines, terminated by
  `data: [DONE]`), extracts `delta.content`, feeds it through the redactor, and yields
  whatever comes out as plain-text chunks to the client.

## Design notes / limitations

- The tail size is sized to the *longest fixed-length pattern* (SSN/card, ~20-24 chars),
  not to email — email has no hard upper bound, so a sufficiently long email address
  could in theory still straddle two flush boundaries beyond the 64-char window. This is
  a deliberate tradeoff: buffering the *entire* message to fully guarantee email safety
  would defeat the point of streaming (time-to-first-token).
- The guardrail re-scans the buffer's tail on every `feed()` call rather than maintaining
  incremental match state — simpler, and cheap at these buffer sizes, but wouldn't scale
  to very high-throughput multi-tenant use without further optimization.

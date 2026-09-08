# Task 4 — SQLite Rate Limiter + Model Fallback

A FastAPI gateway in front of two LLM providers that (a) enforces a per-tenant sliding-window
token budget backed by SQLite, and (b) transparently fails over to a secondary provider when
the primary is rate-limited, times out, or is unreachable.

```
client --Bearer <tenant>--> gateway (:8002) --> primary (:9200)
                                             \-> secondary (:9300)  [on 429 / timeout / network error]
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
# terminal 1 — mock primary provider (supports /set_mode/{ok,429,timeout,500})
uvicorn examples.mock_primary:app --port 9200

# terminal 2 — mock secondary provider
uvicorn examples.mock_secondary:app --port 9300

# terminal 3 — the gateway
uvicorn app.main:app --port 8002
```

Then, from the `task_04_llm_rate_limit_fallback` directory, run the scripted walkthrough
(exercises the happy path, rate-limit rejection, and all three failover triggers):

```powershell
powershell -File examples\try_gateway.ps1
```

## Test

```bash
pytest
```

`tests/test_rate_limiter.py` exercises the SQLite limiter directly (window expiry,
concurrent consumption, per-tenant isolation); `tests/test_gateway.py` drives the full
endpoint with mocked provider responses.

## How it works

- **`app/rate_limiter.py`** (`SQLiteTokenRateLimiter`) — a sliding-window limiter: each
  request's token cost is logged as a row (`tenant_id, tokens, timestamp`) in SQLite; on
  each call, expired rows (older than the window) are deleted and the remaining sum for
  that tenant is compared against the limit inside a single `BEGIN IMMEDIATE` transaction,
  so concurrent requests from the same tenant can't both slip past the limit. WAL mode is
  enabled for read/write concurrency across the (few) worker threads `asyncio.to_thread`
  hands this off to.
- **`app/token_counter.py`** — a cheap token estimate (`chars / 4 + max_tokens`) used to
  charge the budget *before* calling a provider, so a request can be rejected without
  spending any provider capacity on it.
- **`app/model_router.py`** (`ModelRouter`) — calls the primary; on a `429` or a
  timeout/connection error, retries once against the secondary. A `5xx` from the primary
  is *not* treated as a failover trigger (see below) — it's surfaced as a `503` instead.
- **`app/providers.py`** — thin `httpx` wrapper with a 3-second timeout per call.
- **`app/main.py`** — wires it together: auth (bearer token = tenant id) → rate check →
  routed completion, attaching `X-RateLimit-*` / `X-Request-ID` / `X-Model-Provider`
  headers throughout, with a consistent `{"error": {code, message, request_id}}` envelope
  on every failure path.

## Design notes

- **Only `429` and network-level failures (timeout/connection error) trigger failover.**
  A `5xx` from the primary is treated as a real backend error, not a "try elsewhere"
  signal — flipping every 500 to the secondary would silently mask a genuinely broken
  primary. `examples/mock_primary.py`'s `/set_mode/500` case demonstrates this: the
  gateway is expected to return `503`, not transparently succeed via the secondary.
- **Tenant identity is the bearer token itself** (no real auth backend) — good enough to
  demonstrate per-tenant isolation in the rate limiter without building out a full
  identity layer for the assessment.
- **Token accounting happens before the call, using an estimate**, not the provider's
  actual usage from its response — trades a small amount of accuracy for not needing to
  await the provider before enforcing the budget.

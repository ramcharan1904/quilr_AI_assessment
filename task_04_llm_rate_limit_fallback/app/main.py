import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from .rate_limiter import SQLiteTokenRateLimiter
from .model_router import ModelRouter
from .token_counter import estimate_tokens
from .errors import gateway_error

PRIMARY = "http://127.0.0.1:9200/v1/chat/completions"
SECONDARY = "http://127.0.0.1:9300/v1/chat/completions"
limiter = SQLiteTokenRateLimiter()
router = ModelRouter(PRIMARY, SECONDARY)

@asynccontextmanager
async def lifespan(app):
    yield
    await router.close()

app = FastAPI(title="LLM Gateway", lifespan=lifespan)

@app.post("/v1/chat/completions")
async def completion(request: Request,
                     authorization: str | None = Header(default=None)):
    request_id = request.headers.get("X-Request-ID", f"req-{time.time_ns()}")
    if not authorization or not authorization.startswith("Bearer "):
        return gateway_error(401, "invalid_api_key", "Authentication failed.", request_id)

    tenant = authorization[7:].strip()
    try:
        payload = await request.json()
        tokens = estimate_tokens(payload)
    except Exception:
        return gateway_error(400, "invalid_request", "The request body is invalid.", request_id)

    try:
        allowed, remaining = await limiter.try_consume(tenant, tokens)
    except Exception:
        return gateway_error(503, "rate_limiter_unavailable",
                             "Gateway rate limiter is temporarily unavailable.", request_id)

    if not allowed:
        return JSONResponse(
            content={"error": {"code": "rate_limit_exceeded",
                                "message": "Token rate limit exceeded.",
                                "request_id": request_id}},
            status_code=429,
            headers={"Retry-After": "60",
                     "X-RateLimit-Limit": str(limiter.limit),
                     "X-RateLimit-Remaining": str(remaining)})

    response, provider = await router.complete(payload)
    if response is None:
        return gateway_error(503, "model_unavailable",
                             "The requested model is temporarily unavailable.", request_id)

    try:
        body = response.json()
    except ValueError:
        return gateway_error(502, "invalid_upstream_response",
                             "The model provider returned an invalid response.", request_id)

    return JSONResponse(content=body, status_code=200, headers={
        "X-Request-ID": request_id,
        "X-Model-Provider": provider,
        "X-RateLimit-Limit": str(limiter.limit),
        "X-RateLimit-Remaining": str(remaining),
    })

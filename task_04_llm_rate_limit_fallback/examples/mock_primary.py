"""Stand-in primary LLM provider for manually exercising the gateway.

Not part of the graded deliverable - the real target is app/main.py, which
routes to whatever PRIMARY/SECONDARY URLs are configured in app/main.py
(defaults: 127.0.0.1:9200 and 127.0.0.1:9300). Lets you flip its behavior at
runtime via /set_mode/<mode> to trigger each failover path on demand:
  ok      - normal successful response (default)
  429     - returns 429, gateway should fail over to the secondary
  timeout - sleeps 10s, gateway should time out at 3000ms and fail over
  500     - returns 500, gateway should NOT fail over (only 429/timeout do)
"""
import asyncio

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()
MODE = {"value": "ok"}


@app.post("/v1/chat/completions")
async def completions(payload: dict):
    if MODE["value"] == "429":
        return JSONResponse(status_code=429, content={"error": "rate limited"})
    if MODE["value"] == "timeout":
        await asyncio.sleep(10)
        return {"id": "primary-slow"}
    if MODE["value"] == "500":
        return JSONResponse(status_code=500, content={"error": "boom"})
    return {"id": "primary-1", "choices": [{"message": {"content": "hello from primary"}}]}


@app.post("/set_mode/{mode}")
async def set_mode(mode: str):
    MODE["value"] = mode
    return {"mode": mode}

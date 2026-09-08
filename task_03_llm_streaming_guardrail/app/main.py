import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from .stream_proxy import stream_provider

app = FastAPI(title="Streaming PII Guardrail")
UPSTREAM = os.getenv("LLM_UPSTREAM_URL",
                     "http://127.0.0.1:9100/v1/chat/completions")

@app.post("/v1/chat/completions")
async def completion(request: Request):
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse(
            content={"error": {"code": "invalid_request",
                                "message": "The request body is invalid."}},
            status_code=400,
        )
    return StreamingResponse(stream_provider(payload, UPSTREAM),
                             media_type="text/plain",
                             headers={"Cache-Control":"no-cache",
                                      "X-Accel-Buffering":"no"})

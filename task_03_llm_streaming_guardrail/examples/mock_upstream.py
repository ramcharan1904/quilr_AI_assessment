"""Stand-in LLM provider for manually exercising the streaming guardrail.

Not part of the graded deliverable - the real target is app/main.py, which
proxies to whatever LLM_UPSTREAM_URL points at. This just emits an SSE stream
containing PII split across small deltas (like a real token-by-token stream
would), so you can watch the guardrail redact it in real time.

Run on its own port, then point the guardrail at it (see README section this
file was added alongside).
"""
import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

TEXT = (
    "Hello! Reach me at alice@example.com, my card is 4111 1111 1111 1111, "
    "and my SSN is 123-45-6789. Thanks for chatting with me today, this is "
    "just some extra padding text so the stream runs long enough to watch."
)
CHUNK_SIZE = 6          # small on purpose - mimics real token-by-token deltas
DELAY_SECONDS = 0.03


@app.post("/v1/chat/completions")
async def completions(payload: dict):
    async def gen():
        for i in range(0, len(TEXT), CHUNK_SIZE):
            event = {"choices": [{"delta": {"content": TEXT[i:i + CHUNK_SIZE]}}]}
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(DELAY_SECONDS)
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")

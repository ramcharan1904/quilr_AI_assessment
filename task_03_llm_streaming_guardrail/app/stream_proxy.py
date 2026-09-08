import json
import httpx
from .stream_buffer import StreamingRedactor

async def stream_provider(payload, url):
    redactor = StreamingRedactor()
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                raw = line[5:].strip() if line.startswith("data:") else line
                if raw == "[DONE]":
                    break
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                delta = event.get("choices",[{}])[0].get("delta",{}).get("content","")
                if delta:
                    safe = redactor.feed(delta)
                    if safe:
                        yield safe
    tail = redactor.flush()
    if tail:
        yield tail

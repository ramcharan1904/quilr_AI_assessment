"""Stand-in secondary (fallback) LLM provider - see mock_primary.py."""
from fastapi import FastAPI

app = FastAPI()


@app.post("/v1/chat/completions")
async def completions(payload: dict):
    return {"id": "secondary-1", "choices": [{"message": {"content": "hello from secondary"}}]}

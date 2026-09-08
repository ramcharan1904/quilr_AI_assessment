import os
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from .auth import authenticate
from .authorization import authorized
from .proxy import forward

app = FastAPI(title="MCP Security Gateway")
DOWNSTREAM = os.getenv("DOWNSTREAM_MCP_URL", "http://127.0.0.1:9000/mcp")

def rpc_error(request_id, code, message):
    return JSONResponse(
        content={"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}},
        status_code=200,
    )

@app.post("/mcp")
async def mcp_proxy(payload: dict, authorization: str | None = Header(default=None)):
    try:
        role = authenticate(authorization)
    except Exception:
        return rpc_error(payload.get("id"), -32000, "Authentication failed")

    method = payload.get("method")
    params = payload.get("params") or {}

    if not authorized(role, method, params):
        return rpc_error(payload.get("id"), -32001, "Unauthorized Tool Call")

    status, body = await forward(payload, DOWNSTREAM)
    return JSONResponse(content=body, status_code=status)

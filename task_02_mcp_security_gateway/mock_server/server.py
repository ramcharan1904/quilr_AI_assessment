from fastapi import FastAPI
app = FastAPI()

@app.post("/mcp")
async def mcp(payload: dict):
    if payload.get("method") == "tools/list":
        return {"jsonrpc":"2.0","id":payload.get("id"),
                "result":{"tools":[{"name":"get_customer_record"},
                                  {"name":"admin_reset_key"}]}}
    if payload.get("method") == "tools/call":
        return {"jsonrpc":"2.0","id":payload.get("id"),
                "result":{"content":[{"type":"text","text":"executed"}]}}
    return {"jsonrpc":"2.0","id":payload.get("id"),
            "error":{"code":-32601,"message":"Method not found"}}

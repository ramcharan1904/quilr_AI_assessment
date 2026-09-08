from fastapi.responses import JSONResponse

def gateway_error(status, code, message, request_id):
    return JSONResponse(status_code=status, content={
        "error": {"code": code, "message": message, "request_id": request_id}
    })

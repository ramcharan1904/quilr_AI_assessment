from fastapi import HTTPException

TOKENS = {"admin-token": "admin", "viewer-token": "viewer"}

def authenticate(header):
    if not header or not header.startswith("Bearer "):
        raise HTTPException(401, "Authentication failed")
    role = TOKENS.get(header[7:].strip())
    if not role:
        raise HTTPException(401, "Authentication failed")
    return role

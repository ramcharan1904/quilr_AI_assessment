def estimate_tokens(payload):
    chars = sum(len(str(m.get("content",""))) for m in payload.get("messages", []))
    return max(1, (chars + 3)//4) + int(payload.get("max_tokens", 256))

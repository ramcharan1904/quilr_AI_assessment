import httpx

async def forward(payload, url):
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(url, json=payload)
        return response.status_code, response.json()

import asyncio, httpx

class ProviderClient:
    def __init__(self, timeout=3.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(timeout))

    async def close(self):
        await self.client.aclose()

    async def call(self, url, payload):
        return await asyncio.wait_for(
            self.client.post(url, json=payload), timeout=self.timeout)

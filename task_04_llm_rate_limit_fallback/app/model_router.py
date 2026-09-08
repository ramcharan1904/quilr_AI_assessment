import asyncio, httpx
from .providers import ProviderClient

class ModelRouter:
    def __init__(self, primary, secondary):
        self.primary, self.secondary = primary, secondary
        self.client = ProviderClient(3.0)

    async def close(self):
        await self.client.close()

    async def complete(self, payload):
        try:
            r = await self.client.call(self.primary, payload)
            if r.status_code == 429:
                return await self._secondary(payload)
            if 200 <= r.status_code < 300:
                return r, "primary"
            return None, "primary_error"
        except (asyncio.TimeoutError, httpx.TimeoutException, httpx.RequestError):
            return await self._secondary(payload)

    async def _secondary(self, payload):
        try:
            r = await self.client.call(self.secondary, payload)
            if 200 <= r.status_code < 300:
                return r, "secondary"
            return None, "secondary_error"
        except (asyncio.TimeoutError, httpx.TimeoutException, httpx.RequestError):
            return None, "secondary_error"

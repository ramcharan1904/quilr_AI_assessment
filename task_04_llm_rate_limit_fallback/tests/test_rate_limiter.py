import asyncio
from app.rate_limiter import SQLiteTokenRateLimiter

def test_concurrent_limit(tmp_path):
    limiter = SQLiteTokenRateLimiter(str(tmp_path/"gateway.db"), 100, 60)
    async def run():
        results = await asyncio.gather(*[
            limiter.try_consume("tenant", 20) for _ in range(10)
        ])
        assert sum(ok for ok, _ in results) == 5
    asyncio.run(run())

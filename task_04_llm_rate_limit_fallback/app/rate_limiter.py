import asyncio, sqlite3, time
from pathlib import Path

class SQLiteTokenRateLimiter:
    def __init__(self, db_path="data/gateway.db", limit=50000, window_seconds=60):
        self.db_path, self.limit, self.window = db_path, limit, window_seconds
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(db_path)
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("""CREATE TABLE IF NOT EXISTS token_events(
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     tenant_id TEXT NOT NULL, tokens INTEGER NOT NULL,
                     timestamp REAL NOT NULL)""")
        c.execute("""CREATE INDEX IF NOT EXISTS idx_events_tenant_time
                     ON token_events(tenant_id,timestamp)""")
        c.commit(); c.close()

    async def try_consume(self, tenant_id, tokens):
        return await asyncio.to_thread(self._consume, tenant_id, tokens)

    def _consume(self, tenant_id, tokens):
        if tokens <= 0: raise ValueError("tokens must be positive")
        if tokens > self.limit: return False, 0
        now, cutoff = time.time(), time.time() - self.window
        c = sqlite3.connect(self.db_path, timeout=5)
        c.execute("PRAGMA busy_timeout=5000")
        try:
            c.execute("BEGIN IMMEDIATE")
            c.execute("DELETE FROM token_events WHERE tenant_id=? AND timestamp<=?",
                      (tenant_id, cutoff))
            used = c.execute(
                "SELECT COALESCE(SUM(tokens),0) FROM token_events "
                "WHERE tenant_id=? AND timestamp>?", (tenant_id, cutoff)
            ).fetchone()[0]
            if used + tokens > self.limit:
                c.rollback()
                return False, max(0, self.limit-used)
            c.execute("INSERT INTO token_events(tenant_id,tokens,timestamp) VALUES(?,?,?)",
                      (tenant_id, tokens, now))
            c.commit()
            return True, self.limit-used-tokens
        except Exception:
            c.rollback()
            raise
        finally:
            c.close()

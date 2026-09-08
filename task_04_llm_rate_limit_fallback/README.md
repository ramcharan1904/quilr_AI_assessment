# Task 4 — Rate Limiting & Model Fallback
- SQLite on disk
- 50,000 tokens / tenant / 60 seconds
- Primary timeout: 3000 ms
- Primary HTTP 429 => secondary
- Sanitized gateway errors
- SQLite BEGIN IMMEDIATE prevents concurrent over-allocation

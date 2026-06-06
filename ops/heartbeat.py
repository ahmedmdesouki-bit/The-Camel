"""
Machine heartbeat (S6) — proof the operator is alive.

`beat()` stamps a single-row heartbeat; `is_alive()` checks staleness against an injected
`now` (pure, testable). The scheduler beats each tick; monitoring alerts if the heartbeat
goes stale (machine down / loop hung).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from db.sqlite import connection

DEFAULT_MAX_AGE_SECONDS = 90 * 60  # 90 minutes


def beat(portfolio_db: str, now: Optional[str] = None) -> str:
    ts = now or datetime.now(timezone.utc).isoformat()
    with connection(portfolio_db) as conn:
        conn.execute(
            "INSERT INTO heartbeat (id, ts) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET ts=excluded.ts", (ts,))
    return ts


def last_beat(portfolio_db: str) -> Optional[str]:
    with connection(portfolio_db) as conn:
        row = conn.execute("SELECT ts FROM heartbeat WHERE id=1").fetchone()
    return row[0] if row else None


def is_alive(portfolio_db: str, now: str, max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS) -> bool:
    last = last_beat(portfolio_db)
    if not last:
        return False
    age = (datetime.fromisoformat(now) - datetime.fromisoformat(last)).total_seconds()
    return 0 <= age <= max_age_seconds

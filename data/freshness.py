"""
Data freshness checker (S4) — Constitution rule #8: no action on stale data.

`now` is injected so the core logic stays pure and testable. `check_symbol_freshness`
reads the latest ingested_at for a symbol from the market DB and compares it to `now`.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from db.sqlite import connection

DEFAULT_MAX_AGE_HOURS = 24.0


@dataclass
class FreshnessResult:
    fresh: bool
    age_hours: Optional[float]
    reason: str


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def is_fresh(ingested_at: str, now: str, max_age_hours: float = DEFAULT_MAX_AGE_HOURS) -> FreshnessResult:
    """Pure check: is `ingested_at` within `max_age_hours` of `now`? (both ISO-8601)."""
    age = (_parse(now) - _parse(ingested_at)).total_seconds() / 3600.0
    if age < 0:
        return FreshnessResult(False, age, "ingested_at is in the future — clock/data anomaly")
    if age > max_age_hours:
        return FreshnessResult(False, age, f"data is {age:.1f}h old (> {max_age_hours}h)")
    return FreshnessResult(True, age, "fresh")


def check_symbol_freshness(
    market_db: str,
    symbol: str,
    now: str,
    max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
) -> FreshnessResult:
    """Read the latest ingested_at for `symbol` and check freshness against `now`."""
    with connection(market_db) as conn:
        row = conn.execute(
            "SELECT ingested_at FROM prices WHERE symbol=? ORDER BY ingested_at DESC LIMIT 1",
            (symbol,),
        ).fetchone()
    if row is None or not row[0]:
        return FreshnessResult(False, None, f"no price data for {symbol}")
    return is_fresh(row[0], now, max_age_hours)

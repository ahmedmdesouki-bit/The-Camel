"""
Earnings-blackout rule (S8/S13) — don't OPEN a new position into an earnings print.

Earnings are a binary, high-variance event the Edge Proof can't price; the conservative rule is to refuse
*opening/adding* a position within `window_days` either side of a known earnings date (reduce-only exits stay
open). This is the pure decision logic; the **earnings-calendar feed is the paid/S15 dependency** (Finnhub
free tier / EODHD), so the calendar is injected — with no calendar, `in_blackout` returns False (the rule is
inert rather than guessing). Wire `is_blocked` into the driver once a calendar source is connected.
"""
from __future__ import annotations

from datetime import date
from typing import Iterable, Optional


def _d(x) -> Optional[date]:
    if x is None or x == "":
        return None
    if isinstance(x, date):
        return x
    try:
        return date.fromisoformat(str(x)[:10])
    except ValueError:
        return None


def in_blackout(earnings_dates: Iterable, as_of, window_days: int = 2) -> bool:
    """True if `as_of` is within `window_days` of any known earnings date (inclusive). Empty/unknown
    calendar → False (inert, never a false positive that blocks legitimate trades)."""
    ref = _d(as_of)
    if ref is None or window_days < 0:
        return False
    for e in earnings_dates or ():
        ed = _d(e)
        if ed is not None and abs((ed - ref).days) <= window_days:
            return True
    return False


def is_blocked(side: str, earnings_dates: Iterable, as_of, window_days: int = 2) -> bool:
    """Block only OPENING/INCREASING sides (buy/increase/add); a reduce-only sell is always allowed."""
    if str(side or "").strip().lower() in {"sell", "close", "reduce", "exit", "trim"}:
        return False
    return in_blackout(earnings_dates, as_of, window_days)

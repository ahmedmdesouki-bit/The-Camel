"""
Fill + slippage models (S12) — pure simulation of a limit order against a quote.

Honest by construction: a buy fills only if its limit crosses the ask (else NO_FILL); the fill price is
the touch you actually pay (ask for a buy, bid for a sell) so you cross the spread; size beyond the
displayed quantity is a PARTIAL fill; a stale or invalid quote is REJECTED (never priced). Fees are
charged in bps. No $1 fallback — that is a loop_test-only convenience and never touches a fill here.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from trader.execution.models import Order, MarketSnapshot, Fill, FillStatus

DEFAULT_FEE_BPS = 1.0          # 0.01% per-side fee estimate
DEFAULT_MAX_AGE_S = 900        # quote older than 15 min → stale → reject


def slippage_bps(snapshot: MarketSnapshot, side: str) -> float:
    """Half-spread crossed, in basis points (the cost of taking liquidity at the touch)."""
    m, sp = snapshot.mid, snapshot.spread_pct
    if m is None or sp is None:
        return 0.0
    return round((sp / 2.0) * 10000.0, 2)


def _age_seconds(as_of: Optional[str], now: Optional[str]) -> Optional[float]:
    if not as_of or not now:
        return None
    try:
        a = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
        n = datetime.fromisoformat(now.replace("Z", "+00:00"))
        return (n - a).total_seconds()
    except (ValueError, TypeError):
        return None


def simulate_fill(order: Order, snapshot: MarketSnapshot, *, fee_bps: float = DEFAULT_FEE_BPS,
                  max_age_s: float = DEFAULT_MAX_AGE_S, now: Optional[str] = None,
                  allow_market: bool = False) -> Fill:
    """Simulate one limit order against a quote. Pure."""
    def rejected(reason):
        return Fill(order.symbol, order.side, order.qty, 0.0, 0.0, 0.0, 0.0, FillStatus.REJECTED, reason)

    def no_fill(reason):
        return Fill(order.symbol, order.side, order.qty, 0.0, 0.0, 0.0, 0.0, FillStatus.NO_FILL, reason)

    # 1 limit-orders only (no market orders, no pre/after-hours) unless explicitly opted in
    if order.order_type != "limit" and not allow_market:
        return rejected("market order refused — realistic paper is limit-orders only")
    # 2 stale-data rejection
    age = _age_seconds(snapshot.as_of, now)
    if age is not None and age > max_age_s:
        return rejected(f"stale quote ({age:.0f}s > {max_age_s:.0f}s) — refused, no fabricated price")
    # 3 invalid snapshot
    if snapshot.bid is None or snapshot.ask is None or snapshot.ask <= 0:
        return rejected("no valid bid/ask — refused")

    side = order.side.lower()
    # 4 marketable test — the limit must cross the touch
    if side == "buy":
        if order.limit_price < snapshot.ask:
            return no_fill(f"not marketable: limit {order.limit_price} < ask {snapshot.ask}")
        touch = snapshot.ask
    else:
        if order.limit_price > snapshot.bid:
            return no_fill(f"not marketable: limit {order.limit_price} > bid {snapshot.bid}")
        touch = snapshot.bid

    # 5 partial fill against displayed size
    avail = snapshot.displayed_size if snapshot.displayed_size is not None else order.qty
    filled = min(order.qty, max(0.0, avail))
    if filled <= 0:
        return no_fill("no displayed size")
    status = FillStatus.FILLED if abs(filled - order.qty) < 1e-9 else FillStatus.PARTIAL
    fees = round(touch * filled * (fee_bps / 10000.0), 6)
    return Fill(order.symbol, side, order.qty, filled, round(touch, 6), fees,
                slippage_bps(snapshot, side), status,
                "filled at the touch" if status == FillStatus.FILLED
                else f"partial: {filled} of {order.qty} at displayed size")

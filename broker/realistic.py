"""
broker/realistic.py (S18) — the INVESTMENT-VALID production paper broker.

`PaperBroker` fills BUYS at last close — fine for proving the loop runs, but optimistic for performance
reporting (no spread, no fees, fractional shares). This broker drives the S12 realistic-paper executor on
an end-of-day snapshot synthesized from the latest bar: a BUY crosses a modeled spread, pays fees, is capped
at a fraction of daily volume, and is rounded to WHOLE shares (Sahm). A buy it cannot make honestly — below
one whole share, no bar — is an honest NON-FILL (NoFillError), never a fabricated price. So the track record
it produces is *investment-valid*, the basis the ≥28-run live-readiness clock should count.

SELLS / exits delegate to the last-close PaperBroker on purpose: de-risking a held name must never be blocked
by a modeled spread or a stale-quote rejection (you always want to be able to get OUT). Same `submit()` shape
as PaperBroker, so it is a drop-in for the assembled loop's executor.
"""
from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from db.sqlite import connection
from guardrail.constitution import Action, Decision
from ledger.writer import append_entry, _ensure_table as _ensure_ledger_table
from broker.positions import apply_fill
from broker.paper import PaperBroker, NoMarketPriceError, pre_flight_execution_check
from trader.execution.models import Order, MarketSnapshot, FillStatus
from trader.execution.realistic_paper import RealisticPaperExecutor


class NoFillError(RuntimeError):
    """An honest non-fill from the realistic engine (below one whole share, non-marketable, no size, stale).
    Raised so the assembled loop records a non-fill (execute_error stage) rather than a fabricated trade."""


def _latest_bar(market_db: str, symbol: str):
    with connection(market_db) as conn:
        return conn.execute(
            "SELECT close, volume, ingested_at, date FROM prices WHERE symbol=? ORDER BY date DESC LIMIT 1",
            (symbol,)).fetchone()


class RealisticPaperBroker:
    # EOD bars are ~1 day old by tick time, so the executor's intraday 15-min staleness would reject every
    # bar; 4 days rejects only a genuine gap (the 24h data-freshness gate is the real currency check upstream).
    def __init__(self, portfolio_db: str, market_db: str, *, spread_bps: float = 5.0,
                 capacity_frac: float = 0.01, fee_bps: float = 1.0, max_age_s: float = 345600.0):
        self.portfolio_db = portfolio_db
        self.market_db = market_db
        self.spread_bps = spread_bps
        self.capacity_frac = capacity_frac
        self.executor = RealisticPaperExecutor(fee_bps=fee_bps, max_age_s=max_age_s, whole_shares=True)
        self._paper = PaperBroker(portfolio_db, market_db)      # sells/exits at last close (+ ensures tables)

    def _snapshot(self, symbol: str) -> MarketSnapshot:
        bar = _latest_bar(self.market_db, symbol)
        if bar is None or not bar["close"]:
            raise NoMarketPriceError(f"no validated bar for {symbol!r} — realistic broker refuses to fill")
        close = float(bar["close"])
        half = close * (self.spread_bps / 2.0 / 10000.0)
        vol = float(bar["volume"] or 0)
        return MarketSnapshot(symbol=symbol, bid=round(close - half, 6), ask=round(close + half, 6),
                              last=close, displayed_size=(vol * self.capacity_frac) if vol > 0 else None,
                              as_of=bar["ingested_at"] or bar["date"])

    def submit(self, action: Action, decision: Decision, client_order_id: Optional[str] = None,
               portfolio_id: Optional[str] = None):
        if not decision.allow:
            raise ValueError(f"Order blocked by Constitution: {decision.reason}")
        if (action.side or "").lower() != "buy":
            return self._paper.submit(action, decision, client_order_id, portfolio_id)   # de-risk at last close

        symbol = action.symbol or ""
        snap = self._snapshot(symbol)
        now = datetime.now(timezone.utc).isoformat()
        ask = snap.ask
        qty = math.floor(action.notional_usd / ask) if ask else 0
        if qty < 1:
            raise NoFillError(f"{symbol}: ${action.notional_usd:.2f} < one whole share at ~${ask:.2f} "
                              f"(realistic whole-share constraint — size the per-trade notional up)")
        fill = self.executor.execute(Order(symbol, "buy", float(qty), limit_price=ask, order_type="limit"),
                                     snap, now=now)
        if fill.status not in (FillStatus.FILLED, FillStatus.PARTIAL) or fill.filled_qty <= 0:
            raise NoFillError(f"{symbol}: realistic engine declined ({fill.status.value}: {fill.reason})")

        coid = client_order_id or str(uuid.uuid4())
        pre_flight_execution_check(self.portfolio_db, coid)
        signed = -(fill.filled_qty * fill.fill_price + fill.fees)        # cash out incl. fees
        _ensure_ledger_table(self.portfolio_db)
        with connection(self.portfolio_db) as conn:                      # orders + ledger + positions, one txn
            cur = conn.execute(
                "INSERT INTO orders (client_order_id, symbol, side, qty, status, mode, created_at, "
                "filled_at, fill_price) VALUES (?,?,?,?, 'filled', 'realistic_paper', ?, ?, ?)",
                (coid, symbol, "buy", fill.filled_qty, now, now, fill.fill_price))
            order_id = cur.lastrowid
            append_entry(self.portfolio_db, "BUY", symbol, signed, ref=f"order_{order_id}", conn=conn)
            apply_fill(self.portfolio_db, symbol, "buy", fill.filled_qty, fill.fill_price, conn=conn)
            if portfolio_id:
                from trader.portfolios.holdings import apply_portfolio_fill
                apply_portfolio_fill(None, portfolio_id, symbol, "buy", fill.filled_qty, fill.fill_price,
                                     conn=conn)
        return fill                                                      # carries fees/slippage/status

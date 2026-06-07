"""
Per-portfolio holdings (S11.5) — the portfolio-scoped accounting view that reconciles to the fund.

The global `positions` table (broker/positions.py) stays the fund-level book of record. This adds a
per-portfolio view in `portfolio_holdings` (weighted-average cost per portfolio) so each portfolio is a
real accounting unit, and `reconcile_to_fund` proves the per-portfolio quantities sum to the fund's —
the S11 acceptance criterion ("portfolio-scoped positions that reconcile to the fund"). Paper only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from db.paths import CamelDbs
from db.sqlite import connection


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_portfolio_fill(dbs: CamelDbs, portfolio_id: str, symbol: str, side: str,
                         qty: float, price: float) -> dict:
    """Update one portfolio's holding for a fill (weighted-avg cost on buys; reduce qty on sells).
    Raises ValueError if a sell exceeds the held quantity (no phantom sells, per-portfolio)."""
    side = side.lower()
    if qty <= 0:
        raise ValueError("fill qty must be positive")
    with connection(dbs.portfolio) as conn:
        row = conn.execute(
            "SELECT qty, avg_cost FROM portfolio_holdings WHERE portfolio_id=? AND symbol=?",
            (portfolio_id, symbol)).fetchone()
        cur_qty = row["qty"] if row else 0.0
        cur_cost = row["avg_cost"] if row else 0.0

        if side == "buy":
            new_qty = cur_qty + qty
            new_cost = ((cur_qty * cur_cost) + (qty * price)) / new_qty if new_qty else 0.0
        else:  # sell / reduce
            if qty > cur_qty + 1e-9:
                raise ValueError(f"portfolio sell {qty} exceeds held {cur_qty} for {symbol}")
            new_qty = cur_qty - qty
            new_cost = cur_cost if new_qty > 0 else 0.0

        conn.execute(
            "INSERT INTO portfolio_holdings (portfolio_id, symbol, qty, avg_cost, market_value, updated_at) "
            "VALUES (?,?,?,?,?,?) ON CONFLICT(portfolio_id, symbol) DO UPDATE SET "
            "qty=excluded.qty, avg_cost=excluded.avg_cost, market_value=excluded.market_value, "
            "updated_at=excluded.updated_at",
            (portfolio_id, symbol, new_qty, round(new_cost, 6), round(new_qty * price, 6), _utcnow()),
        )
    return {"portfolio_id": portfolio_id, "symbol": symbol, "qty": new_qty, "avg_cost": round(new_cost, 6)}


def holdings(dbs: CamelDbs, portfolio_id: str) -> List[dict]:
    with connection(dbs.portfolio) as conn:
        return [dict(r) for r in conn.execute(
            "SELECT symbol, qty, avg_cost, market_value FROM portfolio_holdings "
            "WHERE portfolio_id=? AND qty != 0 ORDER BY symbol", (portfolio_id,))]


def fund_rollup(dbs: CamelDbs) -> Dict[str, float]:
    """Sum per-portfolio quantities up to a fund-level qty per symbol."""
    with connection(dbs.portfolio) as conn:
        rows = conn.execute(
            "SELECT symbol, SUM(qty) AS q FROM portfolio_holdings GROUP BY symbol").fetchall()
    return {r["symbol"]: round(r["q"], 6) for r in rows if abs(r["q"]) > 1e-9}


def reconcile_to_fund(dbs: CamelDbs, fund_qty_by_symbol: Dict[str, float],
                      tol: float = 1e-6) -> List[dict]:
    """Return mismatches where Σ(per-portfolio qty) ≠ the fund book qty. Empty list = reconciled."""
    rollup = fund_rollup(dbs)
    out: List[dict] = []
    for symbol in set(rollup) | set(fund_qty_by_symbol):
        pf = rollup.get(symbol, 0.0)
        fund = fund_qty_by_symbol.get(symbol, 0.0)
        if abs(pf - fund) > tol:
            out.append({"symbol": symbol, "portfolio_sum": pf, "fund_qty": fund,
                        "diff": round(pf - fund, 6)})
    return out

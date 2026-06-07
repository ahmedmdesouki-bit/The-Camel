"""
Position accounting (S6.6) — keep camel_portfolio.db `positions` in sync on every fill.

The PaperBroker writes orders + ledger; this maintains the positions table so that:
  - the phantom-sell guard is EXACT (qty-based, not value-based),
  - paper P&L (realized + unrealized) is real,
  - holdings reconcile with ledger cash.

BUY  — create/increase qty with a weighted-average cost.
SELL — validate qty <= held, reduce qty, realize P&L = (price - avg_cost) * sell_qty; close at zero.

This module is the single writer of the `positions` table. Pure SQL + arithmetic, no network.
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from db.sqlite import connection

_EPS = 1e-9


class InsufficientPositionError(RuntimeError):
    """Raised when a sell exceeds the held quantity (exact qty-based phantom guard)."""


@dataclass
class Position:
    symbol: str
    qty: float
    avg_cost: float
    market_price: float
    market_value: float
    realized_pnl: float
    status: str           # open | closed


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_position(r) -> Position:
    return Position(
        symbol=r["symbol"], qty=r["qty"] or 0.0, avg_cost=r["avg_cost"] or 0.0,
        market_price=r["market_price"] or 0.0, market_value=r["market_value"] or 0.0,
        realized_pnl=r["realized_pnl"] or 0.0, status=r["status"] or "open",
    )


def get_position(portfolio_db: str, symbol: str) -> Optional[Position]:
    with connection(portfolio_db) as conn:
        r = conn.execute(
            "SELECT symbol, qty, avg_cost, market_price, market_value, realized_pnl, status "
            "FROM positions WHERE symbol=?", (symbol,),
        ).fetchone()
    return _row_to_position(r) if r is not None else None


def held_qty(portfolio_db: str, symbol: str) -> float:
    p = get_position(portfolio_db, symbol)
    return p.qty if p else 0.0


def all_positions(portfolio_db: str, open_only: bool = True) -> List[Position]:
    q = ("SELECT symbol, qty, avg_cost, market_price, market_value, realized_pnl, status "
         "FROM positions")
    if open_only:
        q += " WHERE status='open' AND qty > 0"
    with connection(portfolio_db) as conn:
        rows = conn.execute(q).fetchall()
    return [_row_to_position(r) for r in rows]


def positions_market_value(portfolio_db: str) -> float:
    """Total market value of open positions (at last fill price)."""
    return sum(p.market_value for p in all_positions(portfolio_db))


def apply_fill(portfolio_db: str, symbol: str, side: str, qty: float, price: float,
               conn: Optional[sqlite3.Connection] = None) -> Position:
    """
    Update `positions` for one fill and return the resulting Position.
    Raises InsufficientPositionError if a SELL exceeds the held quantity.

    **Atomicity (P1-A):** pass an open `conn` to enlist this update in a caller-owned transaction
    (so a phantom-sell raise rolls back the order + ledger writes too). With `conn=None` the
    behaviour is unchanged (own connection + own commit).
    """
    side = side.lower()
    if qty <= 0:
        raise ValueError("fill qty must be positive")
    now = _now()
    if conn is not None:
        return _apply_on_conn(conn, symbol, side, qty, price, now)
    with connection(portfolio_db) as own:
        return _apply_on_conn(own, symbol, side, qty, price, now)


def _apply_on_conn(conn: sqlite3.Connection, symbol: str, side: str, qty: float,
                   price: float, now: str) -> Position:
    """The fill math + positions upsert, on an existing connection (no commit here)."""
    r = conn.execute(
        "SELECT qty, avg_cost, realized_pnl, opened_at FROM positions WHERE symbol=?",
        (symbol,),
    ).fetchone()
    held = (r["qty"] if r else 0.0) or 0.0
    avg = (r["avg_cost"] if r else 0.0) or 0.0
    realized = (r["realized_pnl"] if r else 0.0) or 0.0
    opened_at = (r["opened_at"] if r and r["opened_at"] else now)

    if side == "buy":
        new_qty = held + qty
        new_avg = (held * avg + qty * price) / new_qty if new_qty > _EPS else 0.0
    elif side == "sell":
        if qty > held + _EPS:
            raise InsufficientPositionError(
                f"sell {qty:.6f} {symbol} exceeds held {held:.6f}")
        realized += (price - avg) * qty
        new_qty = held - qty
        new_avg = avg if new_qty > _EPS else 0.0
    else:
        raise ValueError(f"unknown side {side!r}")

    status = "open" if new_qty > _EPS else "closed"
    market_value = new_qty * price
    unrealized = (price - new_avg) * new_qty if new_qty > _EPS else 0.0

    conn.execute(
        "INSERT INTO positions "
        "(symbol, qty, avg_cost, market_price, market_value, unrealized_pnl, "
        " realized_pnl, opened_at, updated_at, status) "
        "VALUES (?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(symbol) DO UPDATE SET "
        "qty=excluded.qty, avg_cost=excluded.avg_cost, market_price=excluded.market_price, "
        "market_value=excluded.market_value, unrealized_pnl=excluded.unrealized_pnl, "
        "realized_pnl=excluded.realized_pnl, updated_at=excluded.updated_at, status=excluded.status",
        (symbol, new_qty, new_avg, price, market_value, unrealized, realized, opened_at, now, status),
    )
    return Position(symbol, new_qty, new_avg, price, market_value, realized, status)

"""
PaperBroker — Phase-0 simulated fills.

Fills at the last known close price from the prices table
(fallback: $1.00 so the loop can run without real price data).
Every fill writes to orders + ledger; no real money moves.
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from guardrail.constitution import Action, Decision
from ledger.writer import append_entry


def _last_close(db_path: str, symbol: str) -> Optional[float]:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT close FROM prices WHERE symbol=? ORDER BY date DESC LIMIT 1",
            (symbol,),
        ).fetchone()
    return float(row[0]) if row and row[0] else None


def _ensure_orders_table(db_path: str) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol      TEXT,
                side        TEXT,
                qty         REAL,
                type        TEXT DEFAULT 'market',
                limit_price REAL,
                status      TEXT,
                broker      TEXT DEFAULT 'paper',
                mode        TEXT DEFAULT 'paper',
                approval_id TEXT,
                thesis_id   TEXT,
                created_at  TEXT,
                filled_at   TEXT,
                fill_price  REAL
            )
        """)


@dataclass
class Fill:
    order_id: int
    symbol: str
    side: str
    qty: float
    fill_price: float
    notional: float


class PaperBroker:
    """Phase-0 simulated broker — no real capital."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        _ensure_orders_table(db_path)

    def submit(self, action: Action, decision: Decision) -> Fill:
        """
        Simulate a fill.  Constitution decision must already be allow=True.
        Returns a Fill; writes to orders + ledger.
        """
        if not decision.allow:
            raise ValueError(f"Order blocked by Constitution: {decision.reason}")

        symbol = action.symbol or ""
        notional = action.notional_usd
        fill_price = _last_close(self.db_path, symbol) or 1.0
        qty = notional / fill_price if fill_price else 0.0
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO orders "
                "(symbol, side, qty, status, mode, created_at, filled_at, fill_price) "
                "VALUES (?, ?, ?, 'filled', 'paper', ?, ?, ?)",
                (symbol, action.side, qty, now, now, fill_price),
            )
            order_id = cur.lastrowid

        ledger_type = "BUY" if action.side.lower() == "buy" else "SELL"
        signed_amount = notional if action.side.lower() == "buy" else -notional
        append_entry(self.db_path, ledger_type, symbol,
                     signed_amount, ref=f"order_{order_id}")

        return Fill(
            order_id=order_id, symbol=symbol, side=action.side,
            qty=qty, fill_price=fill_price, notional=notional,
        )

    def paper_balance(self) -> float:
        """Running net cash from fills (negative = deployed)."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT balance_after FROM ledger ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row[0] if row else 0.0

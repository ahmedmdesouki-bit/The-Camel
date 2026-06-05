"""
PaperBroker — Phase-0 simulated fills.

Takes two DB paths:
  portfolio_db  orders + ledger writes
  market_db     last close price lookup

Fills at the last known close price (fallback $1 when no price data).
Every fill writes to orders + ledger; no real money moves.

Cash convention (matches ledger/writer.py): a BUY records a NEGATIVE ledger amount
(cash leaves the fund to buy shares); a SELL records a POSITIVE amount (cash returns).
This keeps the ledger's running `balance_after` a true cash balance that reconciles
against a broker cash statement.
"""
from __future__ import annotations
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from db.sqlite import connection
from guardrail.constitution import Action, Decision
from ledger.writer import append_entry


class DuplicateOrderException(Exception):
    """Raised when an order with the same client_order_id was already submitted (idempotency)."""


def _order_exists(portfolio_db: str, client_order_id: str) -> bool:
    with connection(portfolio_db) as conn:
        row = conn.execute(
            "SELECT 1 FROM orders WHERE client_order_id=? LIMIT 1", (client_order_id,)
        ).fetchone()
    return row is not None


def pre_flight_execution_check(portfolio_db: str, client_order_id: str) -> None:
    """
    Idempotency guard (S4): refuse to submit an order whose client_order_id is already on
    record. Protects against duplicate intents from network dropouts / retries. (For live,
    LiveBroker will also reconcile against the broker's open-orders book before this.)
    """
    if _order_exists(portfolio_db, client_order_id):
        raise DuplicateOrderException(
            f"Duplicate order intent {client_order_id!r} — already submitted."
        )


def _last_close(market_db: str, symbol: str) -> Optional[float]:
    with connection(market_db) as conn:
        row = conn.execute(
            "SELECT close FROM prices WHERE symbol=? ORDER BY date DESC LIMIT 1",
            (symbol,),
        ).fetchone()
    return float(row[0]) if row and row[0] else None


def _ensure_orders_table(portfolio_db: str) -> None:
    # Canonical schema for `orders` lives in db/portfolio.py; this defensive
    # CREATE IF NOT EXISTS only lets the broker run before init_all() has been called.
    with connection(portfolio_db) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                client_order_id TEXT UNIQUE,
                symbol          TEXT,
                side            TEXT,
                qty             REAL,
                type            TEXT DEFAULT 'market',
                limit_price     REAL,
                status          TEXT,
                broker          TEXT DEFAULT 'paper',
                mode            TEXT DEFAULT 'paper',
                approval_id     TEXT,
                thesis_id       TEXT,
                created_at      TEXT,
                filled_at       TEXT,
                fill_price      REAL
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
    client_order_id: str = ""
    # Phase-0 fills are simulated at last close — never mistake this for real execution.
    execution_quality: str = "simulated_unrealistic"
    fill_model: str = "last_close"


class PaperBroker:
    """Phase-0 simulated broker — no real capital."""

    def __init__(self, portfolio_db: str, market_db: str):
        self.portfolio_db = portfolio_db
        self.market_db = market_db
        _ensure_orders_table(portfolio_db)

    def submit(self, action: Action, decision: Decision,
               client_order_id: Optional[str] = None) -> Fill:
        """
        Simulate a fill.  Constitution decision must be allow=True.
        Idempotent: a stable client_order_id is generated if not supplied, and a repeat of
        the same id is refused (DuplicateOrderException). Writes to orders + ledger
        (BUY = cash out, SELL = cash in).
        """
        if not decision.allow:
            raise ValueError(f"Order blocked by Constitution: {decision.reason}")

        coid = client_order_id or str(uuid.uuid4())
        pre_flight_execution_check(self.portfolio_db, coid)   # idempotency guard

        symbol = action.symbol or ""
        notional = action.notional_usd
        fill_price = _last_close(self.market_db, symbol) or 1.0
        qty = notional / fill_price if fill_price else 0.0
        now = datetime.now(timezone.utc).isoformat()

        with connection(self.portfolio_db) as conn:
            cur = conn.execute(
                "INSERT INTO orders "
                "(client_order_id, symbol, side, qty, status, mode, created_at, filled_at, fill_price) "
                "VALUES (?, ?, ?, ?, 'filled', 'paper', ?, ?, ?)",
                (coid, symbol, action.side, qty, now, now, fill_price),
            )
            order_id = cur.lastrowid

        is_buy = action.side.lower() == "buy"
        ledger_type = "BUY" if is_buy else "SELL"
        signed = -notional if is_buy else notional   # BUY = cash out, SELL = cash in
        append_entry(self.portfolio_db, ledger_type, symbol,
                     signed, ref=f"order_{order_id}")

        return Fill(
            order_id=order_id, symbol=symbol, side=action.side,
            qty=qty, fill_price=fill_price, notional=notional, client_order_id=coid,
        )

    def paper_balance(self) -> float:
        """Running ledger cash balance (DEPOSIT/SELL add, BUY subtracts)."""
        with connection(self.portfolio_db) as conn:
            row = conn.execute(
                "SELECT balance_after FROM ledger ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row[0] if row else 0.0

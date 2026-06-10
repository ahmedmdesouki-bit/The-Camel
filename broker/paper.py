"""
PaperBroker — Phase-0 simulated fills.

Takes two DB paths:
  portfolio_db  orders + ledger writes
  market_db     last close price lookup

Fills at the last known close price. The legacy $1 fallback is now refused by default
(S6.5): with no price data, `submit` raises NoMarketPriceError instead of inventing a
price — so no performance number can ever come from a fabricated fill. The fallback is
available only when a caller explicitly opts in (`allow_fallback_price=True`, unit tests
only), and such fills are stamped `fill_model="fallback_dollar"` so they are never mistaken
for real execution. Every fill writes to orders + ledger; no real money moves.

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
from ledger.writer import append_entry, _ensure_table as _ensure_ledger_table
from broker.positions import apply_fill, held_qty, InsufficientPositionError
from trader.portfolios.holdings import apply_portfolio_fill


class DuplicateOrderException(Exception):
    """Raised when an order with the same client_order_id was already submitted (idempotency)."""


class NoMarketPriceError(RuntimeError):
    """Raised (S6.5) when no validated close price exists and the $1 fallback is not allowed.

    Refusing to fill at a fabricated price is the point: a performance number must never come
    from a fallback fill. Unit tests that need a fill without seeding a price opt in via
    `PaperBroker(..., allow_fallback_price=True)`.
    """


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

    def __init__(self, portfolio_db: str, market_db: str,
                 allow_fallback_price: bool = False):
        self.portfolio_db = portfolio_db
        self.market_db = market_db
        # S6.5: production refuses the $1 fallback; only unit tests opt in.
        self.allow_fallback_price = allow_fallback_price
        _ensure_orders_table(portfolio_db)

    def submit(self, action: Action, decision: Decision,
               client_order_id: Optional[str] = None,
               portfolio_id: Optional[str] = None) -> Fill:
        """
        Simulate a fill.  Constitution decision must be allow=True.
        Idempotent: a stable client_order_id is generated if not supplied, and a repeat of
        the same id is refused (DuplicateOrderException). Writes to orders + ledger
        (BUY = cash out, SELL = cash in).

        `portfolio_id` (S12): when supplied, the per-portfolio book (`portfolio_holdings`) is updated in
        the SAME transaction as orders + ledger + positions, so the fund book and the portfolio book can
        never diverge from a fill.
        """
        if not decision.allow:
            raise ValueError(f"Order blocked by Constitution: {decision.reason}")

        coid = client_order_id or str(uuid.uuid4())
        pre_flight_execution_check(self.portfolio_db, coid)   # idempotency guard

        symbol = action.symbol or ""
        notional = action.notional_usd

        close = _last_close(self.market_db, symbol)
        if close is not None:
            fill_price, fill_model = close, "last_close"
        elif self.allow_fallback_price:
            # unit-test-only path — clearly stamped so it can never count as real execution
            fill_price, fill_model = 1.0, "fallback_dollar"
        else:
            raise NoMarketPriceError(
                f"No validated close price for {symbol!r}; refusing to fill at a fabricated "
                f"price (pass allow_fallback_price=True in tests to override)."
            )
        qty = notional / fill_price if fill_price else 0.0
        now = datetime.now(timezone.utc).isoformat()

        # S6.6: exact qty-based phantom-sell guard — the broker knows the positions table.
        # (The Constitution's value-based guard is the first wall; this is the precise second wall.)
        if action.side.lower() == "sell":
            have = held_qty(self.portfolio_db, symbol)
            # S16 full-close clamp: a sell within a hair of the whole position IS a full close —
            # the caller sized it from qty×price and float round-trips (notional/fill_price) can land
            # ±1 ulp either side of `have`. Clamping kills both failure modes: an honest close being
            # refused as a phantom sell, and a dust residue that never reaches status='closed' (so the
            # round-trip never resolves and nothing is learned). The guard below still rejects any
            # genuine oversell — the clamp window is relative-1e-6, the guard stays absolute-1e-9.
            if have > 0 and abs(qty - have) <= have * 1e-6:
                qty = have
            if qty > have + 1e-9:
                raise InsufficientPositionError(
                    f"sell {qty:.6f} {symbol} exceeds held {have:.6f}")

        is_buy = action.side.lower() == "buy"
        if not is_buy:
            # cash received = the ACTUAL shares sold × fill price, so after a full-close clamp the ledger
            # entry and the position delta stay exactly consistent (no dust between cash and shares).
            # For an unclamped sell this equals the requested notional anyway. (S16 QA)
            notional = qty * fill_price
        ledger_type = "BUY" if is_buy else "SELL"
        signed = -notional if is_buy else notional   # BUY = cash out, SELL = cash in

        # P1-A: orders + ledger + positions in ONE transaction. If apply_fill raises (e.g. a
        # phantom-sell re-check), the order row and the ledger cash entry roll back too — the
        # books can never diverge from a mid-sequence failure. (Tables ensured first, outside
        # the atomic block, so no nested connection deadlocks under WAL.)
        _ensure_ledger_table(self.portfolio_db)
        with connection(self.portfolio_db) as conn:
            cur = conn.execute(
                "INSERT INTO orders "
                "(client_order_id, symbol, side, qty, status, mode, created_at, filled_at, fill_price) "
                "VALUES (?, ?, ?, ?, 'filled', 'paper', ?, ?, ?)",
                (coid, symbol, action.side, qty, now, now, fill_price),
            )
            order_id = cur.lastrowid
            append_entry(self.portfolio_db, ledger_type, symbol, signed,
                         ref=f"order_{order_id}", conn=conn)
            # keep the positions table in sync — weighted-avg cost on buy, realized P&L on sell.
            apply_fill(self.portfolio_db, symbol, action.side, qty, fill_price, conn=conn)
            # S12: when a portfolio is named, update its per-portfolio book in the SAME transaction.
            if portfolio_id:
                apply_portfolio_fill(None, portfolio_id, symbol, action.side, qty, fill_price, conn=conn)

        return Fill(
            order_id=order_id, symbol=symbol, side=action.side,
            qty=qty, fill_price=fill_price, notional=notional, client_order_id=coid,
            fill_model=fill_model,
        )

    def paper_balance(self) -> float:
        """Running ledger cash balance (DEPOSIT/SELL add, BUY subtracts)."""
        with connection(self.portfolio_db) as conn:
            row = conn.execute(
                "SELECT balance_after FROM ledger ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row[0] if row else 0.0

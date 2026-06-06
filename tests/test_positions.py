"""
S6.6 — position accounting on every fill.

Positions table is maintained by broker/positions.apply_fill: weighted-average cost on buys,
realized P&L on sells, exact qty-based phantom guard, reconcile with ledger cash.
"""
import sqlite3
import pytest

from broker.positions import (
    apply_fill, get_position, held_qty, all_positions, positions_market_value,
    InsufficientPositionError,
)
from broker.paper import PaperBroker
from guardrail.constitution import Action, ActionType, Decision, Thesis
from data.store import store_price
from ledger.writer import append_entry


# ---------------- unit: apply_fill arithmetic ----------------

def test_buy_creates_position(dbs):
    p = apply_fill(dbs.portfolio, "SPUS", "buy", qty=10, price=50.0)
    assert p.qty == pytest.approx(10) and p.avg_cost == pytest.approx(50.0)
    assert p.status == "open" and p.market_value == pytest.approx(500.0)

def test_second_buy_updates_weighted_average_cost(dbs):
    apply_fill(dbs.portfolio, "SPUS", "buy", qty=10, price=50.0)
    p = apply_fill(dbs.portfolio, "SPUS", "buy", qty=10, price=70.0)
    assert p.qty == pytest.approx(20) and p.avg_cost == pytest.approx(60.0)   # (500+700)/20

def test_partial_sell_reduces_qty_and_realizes_pnl(dbs):
    apply_fill(dbs.portfolio, "SPUS", "buy", qty=10, price=50.0)
    p = apply_fill(dbs.portfolio, "SPUS", "sell", qty=4, price=60.0)
    assert p.qty == pytest.approx(6)
    assert p.avg_cost == pytest.approx(50.0)                 # basis unchanged on partial sell
    assert p.realized_pnl == pytest.approx((60 - 50) * 4)    # +40
    assert p.status == "open"

def test_full_sell_closes_position(dbs):
    apply_fill(dbs.portfolio, "SPUS", "buy", qty=10, price=50.0)
    p = apply_fill(dbs.portfolio, "SPUS", "sell", qty=10, price=55.0)
    assert p.qty == pytest.approx(0) and p.status == "closed"
    assert p.realized_pnl == pytest.approx(50.0)             # (55-50)*10
    assert all_positions(dbs.portfolio) == []               # open_only filters it out

def test_oversell_raises(dbs):
    apply_fill(dbs.portfolio, "SPUS", "buy", qty=5, price=50.0)
    with pytest.raises(InsufficientPositionError):
        apply_fill(dbs.portfolio, "SPUS", "sell", qty=6, price=50.0)

def test_sell_without_position_raises(dbs):
    with pytest.raises(InsufficientPositionError):
        apply_fill(dbs.portfolio, "GHOST", "sell", qty=1, price=10.0)

def test_held_qty_helper(dbs):
    assert held_qty(dbs.portfolio, "SPUS") == 0.0
    apply_fill(dbs.portfolio, "SPUS", "buy", qty=3, price=10.0)
    assert held_qty(dbs.portfolio, "SPUS") == pytest.approx(3)


# ---------------- integration: broker keeps positions in sync ----------------

def _seed_price(dbs, symbol="SPUS", close=50.0):
    store_price(dbs.market, dict(symbol=symbol, date="2026-06-04", open=close, high=close,
                                 low=close, close=close, volume=100_000, adj_close=close),
                source="alpaca")

def _buy(symbol="SPUS", notional=500.0):
    return Action(type=ActionType.TRADE, symbol=symbol, side="buy", notional_usd=notional,
                  instrument_type="etf", thesis=Thesis("x", "y", "z"), mode="paper")

def _sell(symbol="SPUS", notional=200.0):
    return Action(type=ActionType.TRADE, symbol=symbol, side="sell", notional_usd=notional,
                  instrument_type="etf", mode="paper")

def test_broker_buy_then_sell_updates_position(dbs):
    _seed_price(dbs, close=50.0)
    b = PaperBroker(dbs.portfolio, dbs.market)
    b.submit(_buy(notional=500.0), Decision(True, "ok"))       # 10 sh @ 50
    assert held_qty(dbs.portfolio, "SPUS") == pytest.approx(10)
    b.submit(_sell(notional=200.0), Decision(True, "ok"))      # sell 4 sh @ 50
    assert held_qty(dbs.portfolio, "SPUS") == pytest.approx(6)

def test_broker_phantom_sell_blocked_at_broker(dbs):
    _seed_price(dbs, close=50.0)
    b = PaperBroker(dbs.portfolio, dbs.market)
    with pytest.raises(InsufficientPositionError):
        b.submit(_sell(notional=100.0), Decision(True, "ok"))   # nothing held

def test_positions_reconcile_with_ledger_cash(dbs):
    _seed_price(dbs, close=50.0)
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    b = PaperBroker(dbs.portfolio, dbs.market)
    b.submit(_buy(notional=500.0), Decision(True, "ok"))        # cash 1000 -> 500, 10 sh @ 50
    # cash balance + market value of holdings == original equity
    cash = b.paper_balance()
    equity = cash + positions_market_value(dbs.portfolio)
    assert cash == pytest.approx(500.0)
    assert equity == pytest.approx(1000.0)


# ---------------- SQLite WAL mode (S6.6) ----------------

def test_databases_use_wal(dbs):
    with sqlite3.connect(dbs.portfolio) as c:
        mode = c.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal"

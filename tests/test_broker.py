"""
Sprint 3 — PaperBroker tests.
Gate: paper orders fill and write to orders + ledger.
"""
import pytest
import sqlite3
from db.sqlite import init_db
from data.store import store_price
from broker.paper import PaperBroker
from guardrail.constitution import (
    Action, ActionType, Decision, Instrument, PortfolioState, Thesis,
)


@pytest.fixture
def tmp_db(tmp_path):
    db = str(tmp_path / "adam.db")
    init_db(db)
    return db


def good_decision():
    return Decision(allow=True, reason="approved")

def bad_decision():
    return Decision(allow=False, reason="off_whitelist", limit_hit="off_whitelist")

def buy_action(symbol="SPUS", notional=500.0):
    return Action(
        type=ActionType.TRADE, symbol=symbol, side="buy",
        notional_usd=notional, instrument_type="etf",
        thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"),
        mode="paper",
    )


# ─────────────────── basic fills ────────────────────────────────

def test_paper_broker_fills_at_fallback_price(tmp_db):
    broker = PaperBroker(tmp_db)
    fill = broker.submit(buy_action(), good_decision())
    assert fill.symbol == "SPUS"
    assert fill.fill_price == pytest.approx(1.0)   # fallback: no price data
    assert fill.qty == pytest.approx(500.0)         # 500 / 1.0

def test_paper_broker_fills_at_last_close(tmp_db):
    store_price(tmp_db, dict(symbol="SPUS", date="2026-06-04",
                             open=50.0, high=51.0, low=49.5, close=50.0,
                             volume=100_000, adj_close=50.0), source="alpaca")
    broker = PaperBroker(tmp_db)
    fill = broker.submit(buy_action(notional=500.0), good_decision())
    assert fill.fill_price == pytest.approx(50.0)
    assert fill.qty == pytest.approx(10.0)   # 500 / 50

def test_paper_broker_writes_to_orders(tmp_db):
    broker = PaperBroker(tmp_db)
    fill = broker.submit(buy_action(), good_decision())
    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute("SELECT symbol, side, status FROM orders WHERE id=?",
                           (fill.order_id,)).fetchone()
    assert row == ("SPUS", "buy", "filled")

def test_paper_broker_writes_to_ledger(tmp_db):
    broker = PaperBroker(tmp_db)
    broker.submit(buy_action(notional=300.0), good_decision())
    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute(
            "SELECT type, amount FROM ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row[0] == "BUY"
    assert row[1] == pytest.approx(300.0)

def test_paper_broker_rejects_blocked_decision(tmp_db):
    broker = PaperBroker(tmp_db)
    with pytest.raises(ValueError, match="blocked"):
        broker.submit(buy_action(), bad_decision())

def test_paper_broker_sell_writes_negative_to_ledger(tmp_db):
    broker = PaperBroker(tmp_db)
    sell_action = Action(
        type=ActionType.TRADE, symbol="SPUS", side="sell",
        notional_usd=200.0, instrument_type="etf", mode="paper",
    )
    broker.submit(sell_action, good_decision())
    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute(
            "SELECT type, amount FROM ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row[0] == "SELL"
    assert row[1] == pytest.approx(-200.0)

def test_paper_broker_sequential_orders(tmp_db):
    broker = PaperBroker(tmp_db)
    broker.submit(buy_action(notional=100.0), good_decision())
    broker.submit(buy_action(notional=200.0), good_decision())
    with sqlite3.connect(tmp_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert count == 2

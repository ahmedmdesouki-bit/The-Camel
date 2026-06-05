"""
Sprint 3 — PaperBroker tests.
PaperBroker(portfolio_db, market_db) since 7-DB migration.
"""
import pytest
import sqlite3
from data.store import store_price
from broker.paper import PaperBroker
from guardrail.constitution import (
    Action, ActionType, Decision, Instrument, PortfolioState, Thesis,
)


@pytest.fixture
def broker(dbs):
    return PaperBroker(dbs.portfolio, dbs.market)

@pytest.fixture
def portfolio_db(dbs):
    return dbs.portfolio

@pytest.fixture
def market_db(dbs):
    return dbs.market


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

def test_paper_broker_fills_at_fallback_price(broker):
    fill = broker.submit(buy_action(), good_decision())
    assert fill.symbol == "SPUS"
    assert fill.fill_price == pytest.approx(1.0)
    assert fill.qty == pytest.approx(500.0)

def test_paper_broker_fills_at_last_close(dbs):
    store_price(dbs.market, dict(symbol="SPUS", date="2026-06-04",
                                 open=50.0, high=51.0, low=49.5, close=50.0,
                                 volume=100_000, adj_close=50.0), source="alpaca")
    broker = PaperBroker(dbs.portfolio, dbs.market)
    fill = broker.submit(buy_action(notional=500.0), good_decision())
    assert fill.fill_price == pytest.approx(50.0)
    assert fill.qty == pytest.approx(10.0)

def test_paper_broker_writes_to_orders(broker, portfolio_db):
    fill = broker.submit(buy_action(), good_decision())
    with sqlite3.connect(portfolio_db) as conn:
        row = conn.execute(
            "SELECT symbol, side, status FROM orders WHERE id=?", (fill.order_id,)
        ).fetchone()
    assert row == ("SPUS", "buy", "filled")

def test_paper_broker_writes_to_ledger(broker, portfolio_db):
    # BUY is cash OUT → negative ledger amount (cash convention).
    broker.submit(buy_action(notional=300.0), good_decision())
    with sqlite3.connect(portfolio_db) as conn:
        row = conn.execute(
            "SELECT type, amount FROM ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row[0] == "BUY" and row[1] == pytest.approx(-300.0)

def test_paper_broker_rejects_blocked_decision(broker):
    with pytest.raises(ValueError, match="blocked"):
        broker.submit(buy_action(), bad_decision())

def test_paper_broker_sell_writes_positive_to_ledger(broker, portfolio_db):
    # SELL is cash IN → positive ledger amount (cash convention).
    sell = Action(type=ActionType.TRADE, symbol="SPUS", side="sell",
                  notional_usd=200.0, instrument_type="etf", mode="paper")
    broker.submit(sell, good_decision())
    with sqlite3.connect(portfolio_db) as conn:
        row = conn.execute(
            "SELECT type, amount FROM ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row[0] == "SELL" and row[1] == pytest.approx(200.0)

def test_paper_broker_sequential_orders(broker, portfolio_db):
    broker.submit(buy_action(notional=100.0), good_decision())
    broker.submit(buy_action(notional=200.0), good_decision())
    with sqlite3.connect(portfolio_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert count == 2


# ---------------- S4: idempotency (pre-flight duplicate-order check) ----------------

def test_duplicate_client_order_id_rejected(broker, portfolio_db):
    from broker.paper import DuplicateOrderException
    broker.submit(buy_action(), good_decision(), client_order_id="intent-1")
    with pytest.raises(DuplicateOrderException):
        broker.submit(buy_action(), good_decision(), client_order_id="intent-1")
    # the duplicate must NOT have created a second order
    with sqlite3.connect(portfolio_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert count == 1

def test_auto_client_order_id_is_unique(broker):
    f1 = broker.submit(buy_action(), good_decision())
    f2 = broker.submit(buy_action(), good_decision())
    assert f1.client_order_id and f2.client_order_id
    assert f1.client_order_id != f2.client_order_id

def test_fill_carries_realism_marker(broker):
    f = broker.submit(buy_action(), good_decision())
    assert f.execution_quality == "simulated_unrealistic" and f.fill_model == "last_close"

"""P1-A — broker write-atomicity: orders + ledger + positions move together or not at all."""
import pytest

import broker.paper as paper_mod
from broker.paper import PaperBroker
from db.sqlite import connection
from guardrail.constitution import Action, ActionType, Decision, Thesis


def _buy(symbol="SPUS", notional=500.0):
    return Action(type=ActionType.TRADE, symbol=symbol, side="buy", notional_usd=notional,
                  instrument_type="etf",
                  thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"), mode="paper")


def _counts(portfolio_db):
    with connection(portfolio_db) as c:
        orders = c.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        ledger = c.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
        positions = c.execute("SELECT COUNT(*) FROM positions WHERE qty > 0").fetchone()[0]
    return orders, ledger, positions


def test_successful_fill_writes_all_three(dbs):
    b = PaperBroker(dbs.portfolio, dbs.market, allow_fallback_price=True)
    b.submit(_buy(), Decision(allow=True, reason="ok"))
    assert _counts(dbs.portfolio) == (1, 1, 1)   # order + ledger + position all present


def test_position_failure_rolls_back_order_and_ledger(dbs, monkeypatch):
    # Inject a failure in the positions write (the last step) and prove the order + ledger
    # writes are rolled back — the books can never diverge from a mid-sequence crash.
    b = PaperBroker(dbs.portfolio, dbs.market, allow_fallback_price=True)

    def boom(*a, **k):
        raise RuntimeError("simulated positions-write crash")
    monkeypatch.setattr(paper_mod, "apply_fill", boom)

    with pytest.raises(RuntimeError):
        b.submit(_buy(), Decision(allow=True, reason="ok"))

    assert _counts(dbs.portfolio) == (0, 0, 0)   # nothing committed — atomic rollback

"""
S6.5 — Safety & Accounting Hotfix gate.

One file that asserts the sprint's definition of done end-to-end:
  - phantom sells are blocked (cannot sell what you don't hold; cannot oversell)
  - frozen / non-compliant holdings are close-only (sell to de-risk, never buy/increase)
  - a market buy without a passing EdgeReport is rejected by default
  - the PaperBroker refuses the $1 fallback price outside opted-in unit tests
"""
import pytest

from guardrail.constitution import (
    Action, ActionType, Constitution, Instrument, PortfolioState, Thesis,
)
from capital.allocator import Allocator
from broker.paper import PaperBroker, NoMarketPriceError
from engine.edge_proof_v0 import build_edge_report


def _whitelist():
    return {
        "SPUS": Instrument("SPUS", "Diversified", "compliant", on_whitelist=True),
        "FROZEN": Instrument("FROZEN", "Diversified", "compliant", on_whitelist=True, frozen=True),
        "BADCOMP": Instrument("BADCOMP", "Diversified", "non_compliant", on_whitelist=True),
    }

def _state(**kw):
    s = PortfolioState(fund_usd=10_000, cash_usd=5_000, whitelist=_whitelist())
    for k, v in kw.items():
        setattr(s, k, v)
    return s

def _trade(symbol="SPUS", side="buy", notional=400.0, thesis=True):
    return Action(type=ActionType.TRADE, symbol=symbol, side=side, notional_usd=notional,
                  instrument_type="etf", mode="paper",
                  thesis=Thesis("x", "y", "z") if thesis else None)


# ---- gate 1: phantom sells blocked ----

def test_gate_phantom_sell_blocked():
    d = Constitution().evaluate(_trade(side="sell", thesis=False), _state())   # no holdings
    assert not d.allow and d.limit_hit == "no_holdings"

def test_gate_oversell_blocked():
    d = Constitution().evaluate(_trade(side="sell", notional=900.0, thesis=False),
                                _state(positions={"SPUS": 500.0}))
    assert not d.allow and d.limit_hit == "oversell"


# ---- gate 2: frozen / non-compliant are close-only ----

def test_gate_frozen_buy_blocked_but_sell_allowed():
    c = Constitution()
    assert c.evaluate(_trade(symbol="FROZEN", side="buy"), _state()).limit_hit == "frozen"
    assert c.evaluate(_trade(symbol="FROZEN", side="sell", thesis=False),
                      _state(positions={"FROZEN": 800.0})).allow

def test_gate_non_compliant_buy_blocked_but_sell_allowed():
    c = Constitution()
    assert c.evaluate(_trade(symbol="BADCOMP", side="buy"), _state()).limit_hit == "not_compliant"
    assert c.evaluate(_trade(symbol="BADCOMP", side="sell", thesis=False),
                      _state(positions={"BADCOMP": 800.0})).allow


# ---- gate 3: buy needs a passing EdgeReport by default; sell is exempt ----

def test_gate_buy_without_edge_rejected_by_default():
    r = Allocator().request(_trade(side="buy"), _state())
    assert not r.approved and r.decision.limit_hit == "no_edge_proof"

def test_gate_buy_with_strong_edge_allowed():
    strong = build_edge_report("SPUS", "dip", [0.05] * 30, benchmark_return=0.01)
    r = Allocator().request(_trade(side="buy"), _state(), edge_report=strong)
    assert r.approved

def test_gate_sell_exempt_from_edge():
    r = Allocator().request(_trade(side="sell", thesis=False),
                            _state(positions={"SPUS": 1000.0}))
    assert r.approved

def test_gate_non_buy_opening_side_still_requires_edge():
    # hardening: a side string other than the literal "buy" (e.g. "increase"/"add") must NOT skip the
    # edge gate — default-to-require-edge for any non-reducing TRADE.
    for opening in ("increase", "add", "BUY", "long"):
        r = Allocator().request(_trade(side=opening), _state())
        assert not r.approved and r.decision.limit_hit == "no_edge_proof", opening


# ---- gate 4: no fabricated fill prices in production ----

def test_gate_broker_refuses_fallback_in_production(dbs):
    broker = PaperBroker(dbs.portfolio, dbs.market)   # default: fallback NOT allowed
    from guardrail.constitution import Decision
    with pytest.raises(NoMarketPriceError):
        broker.submit(_trade(side="buy"), Decision(allow=True, reason="ok"))

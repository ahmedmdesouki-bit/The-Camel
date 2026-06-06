"""
Sprint 3 — Capital allocator tests.
Rejected requests must be explicit, never silently clamped.
"""
import pytest
from capital.allocator import Allocator
from guardrail.constitution import (
    Action, ActionType, Constitution, Instrument, PortfolioState, Thesis,
)


def base_state(**kw):
    wl = {
        "SPUS": Instrument("SPUS", sector="Diversified",
                            sharia_status="compliant", on_whitelist=True),
    }
    s = PortfolioState(fund_usd=10_000, cash_usd=5_000, whitelist=wl)
    for k, v in kw.items():
        setattr(s, k, v)
    return s

def good_thesis():
    return Thesis(invalidation="x", profit_take="y", time_stop="z")

def buy(symbol="SPUS", notional=500.0, **kw):
    return Action(
        type=ActionType.TRADE, symbol=symbol, side="buy",
        notional_usd=notional, instrument_type="etf",
        thesis=good_thesis(), mode="paper", **kw
    )


# ─────────────────── approval path ──────────────────────────────

def test_valid_request_approved():
    result = Allocator().request(buy(), base_state(), require_edge=False)
    assert result.approved
    assert result.notional_usd == pytest.approx(500.0)

def test_approved_decision_is_allow():
    result = Allocator().request(buy(), base_state(), require_edge=False)
    assert result.decision.allow


# ─────────────────── rejection path ─────────────────────────────

def test_off_whitelist_rejected():
    result = Allocator().request(buy(symbol="AAPL"), base_state(), require_edge=False)
    assert not result.approved
    assert result.notional_usd == pytest.approx(0.0)
    assert result.decision.limit_hit == "off_whitelist"

def test_over_position_cap_rejected():
    # 20% of 10k = 2000; 2001 should fail
    result = Allocator().request(buy(notional=2001.0), base_state(), require_edge=False)
    assert not result.approved
    assert result.decision.limit_hit == "max_position"

def test_rejection_gives_zero_notional():
    # notional is set to 0 on rejection — never silently clamped
    result = Allocator().request(buy(symbol="AAPL"), base_state(), require_edge=False)
    assert result.notional_usd == 0.0

def test_daily_loss_stop_rejects():
    result = Allocator().request(buy(), base_state(day_pnl_pct=-0.06), require_edge=False)
    assert not result.approved
    assert result.decision.limit_hit == "daily_loss_stop"

def test_custom_constitution_respected():
    # Tighter cap via custom constitution
    strict = Constitution({"max_position_pct": 0.05})
    alloc = Allocator(constitution=strict)
    result = alloc.request(buy(notional=600.0), base_state(), require_edge=False)
    # 600 > 5% of 10k = 500 → rejected
    assert not result.approved

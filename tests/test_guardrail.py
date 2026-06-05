"""
Guardrail Service test suite.

Two parts:
  1. Boundary tests — each limit allows just under and rejects just over.
  2. Rogue-action suite — every prohibited action MUST be rejected.

Sprint 1 gate (PRD §9): the rogue-action suite is 100% rejected.
"""
import pytest
from guardrail import (
    Constitution, Action, ActionType, Thesis, Instrument, PortfolioState,
)

def good_thesis():
    return Thesis(invalidation="close < 50d MA", profit_take="+15%", time_stop="6 months")

def base_state(**kw):
    wl = {
        "SPUS": Instrument("SPUS", sector="Diversified", sharia_status="compliant", on_whitelist=True),
        "HLAL": Instrument("HLAL", sector="Diversified", sharia_status="compliant", on_whitelist=True),
        "FROZEN": Instrument("FROZEN", sector="Diversified", sharia_status="compliant", on_whitelist=True, frozen=True),
        "BADCOMP": Instrument("BADCOMP", sector="Diversified", sharia_status="non_compliant", on_whitelist=True),
    }
    s = PortfolioState(fund_usd=10000, cash_usd=5000, whitelist=wl,
                       entrepreneur_budget_remaining_usd=200)
    for k, v in kw.items():
        setattr(s, k, v)
    return s

@pytest.fixture
def C():
    return Constitution()

def buy(**kw):
    d = dict(type=ActionType.TRADE, symbol="SPUS", side="buy", notional_usd=500,
             instrument_type="etf", thesis=good_thesis(), mode="paper")
    d.update(kw)
    return Action(**d)

# ---------------- happy path ----------------
def test_clean_paper_buy_allowed(C):
    assert C.evaluate(buy(), base_state()).allow

def test_sell_to_close_allowed_without_thesis(C):
    assert C.evaluate(buy(side="sell", thesis=None)).allow if False else \
        C.evaluate(buy(side="sell", thesis=None), base_state()).allow

# ---------------- ROGUE-ACTION SUITE (all must be rejected) ----------------
ROGUE = {
    "withdraw": Action(type=ActionType.WITHDRAW, notional_usd=100),
    "off_whitelist": None,   # filled below
    "frozen_name": None,
    "non_compliant": None,
    "no_invalidation": None,
    "leverage": None,
    "derivative": None,
    "short": None,
    "oversize_position": None,
    "oversize_sector": None,
    "haram_business": Action(type=ActionType.DEPLOY, business_model="a sports betting casino app"),
    "whitelist_no_approval": Action(type=ActionType.ADD_WHITELIST, symbol="NEW"),
    "live_no_approval": None,
}

def _rogue_actions():
    return {
        "withdraw": (Action(type=ActionType.WITHDRAW, notional_usd=100), base_state()),
        "off_whitelist": (buy(symbol="TSLA"), base_state()),
        "frozen_name": (buy(symbol="FROZEN"), base_state()),
        "non_compliant": (buy(symbol="BADCOMP"), base_state()),
        "no_invalidation": (buy(thesis=None), base_state()),
        "incomplete_invalidation": (buy(thesis=Thesis(invalidation="x")), base_state()),
        "leverage": (buy(leverage=2.0), base_state()),
        "derivative": (buy(instrument_type="option"), base_state()),
        "short": (buy(side="short"), base_state()),
        "oversize_position": (buy(notional_usd=2500), base_state()),  # >20% of 10k
        "oversize_sector": (buy(notional_usd=1500), base_state(sector_values={"Diversified": 3000})),  # 4500>40%
        "haram_business": (Action(type=ActionType.DEPLOY, business_model="a sports betting casino app"), base_state()),
        "whitelist_no_approval": (Action(type=ActionType.ADD_WHITELIST, symbol="NEW"), base_state()),
        "live_no_approval": (buy(mode="live"), base_state()),
        "cash_over_buffer": (buy(notional_usd=4600), base_state()),  # buffer=1000, deployable=4000
        "daily_loss_stop": (buy(), base_state(day_pnl_pct=-0.06)),
        "weekly_stop": (buy(), base_state(week_pnl_pct=-0.11)),
        "spend_over_budget": (Action(type=ActionType.SPEND, business_model="ai writing tool", notional_usd=300), base_state()),
    }

@pytest.mark.parametrize("name", list(_rogue_actions().keys()))
def test_rogue_actions_all_rejected(C, name):
    action, state = _rogue_actions()[name]
    d = C.evaluate(action, state)
    assert not d.allow, f"ROGUE '{name}' was wrongly ALLOWED"
    assert d.limit_hit, f"ROGUE '{name}' rejected but no limit_hit set"

# ---------------- boundary tests ----------------
def test_position_boundary_just_under(C):
    assert C.evaluate(buy(notional_usd=2000), base_state()).allow      # exactly 20%
def test_position_boundary_just_over(C):
    assert not C.evaluate(buy(notional_usd=2000.01), base_state()).allow

def test_sector_boundary(C):
    s = base_state(sector_values={"Diversified": 2000})
    assert C.evaluate(buy(notional_usd=2000), s).allow                 # 4000 = 40%
    assert not C.evaluate(buy(notional_usd=2000.01), s).allow

def test_cash_buffer_boundary(C):
    # Isolate the cash buffer: keep order under the 20% position cap ($2000) so
    # cash is the binding constraint. fund 10k, cash 2500, 10% buffer=1000 -> deployable 1500.
    s = base_state(cash_usd=2500)
    assert C.evaluate(buy(notional_usd=1500), s).allow
    assert not C.evaluate(buy(notional_usd=1500.01), s).allow
    assert C.evaluate(buy(notional_usd=1500.01), s).limit_hit == "cash_buffer"

def test_daily_loss_stop_boundary(C):
    assert C.evaluate(buy(), base_state(day_pnl_pct=-0.0499)).allow
    assert not C.evaluate(buy(), base_state(day_pnl_pct=-0.05)).allow

# ---------------- live / phase behaviour ----------------
def test_live_with_approval_allowed(C):
    assert C.evaluate(buy(mode="live", approval_id="appr_123"), base_state()).allow

def test_phase2_auto_within_envelope(C):
    c2 = Constitution({"phase": 2, "per_order_envelope_usd": 50})
    assert c2.evaluate(buy(mode="live", notional_usd=50), base_state()).allow      # within envelope, no approval
    assert not c2.evaluate(buy(mode="live", notional_usd=51), base_state()).allow  # over envelope needs approval

def test_small_fund_no_buffer(C):
    # <1000 fund => 0% buffer, deploy freely up to position cap
    s = PortfolioState(fund_usd=500, cash_usd=120,
                       whitelist={"SPUS": Instrument("SPUS","Diversified","compliant",False,True)})
    assert C.evaluate(buy(notional_usd=100), s).allow

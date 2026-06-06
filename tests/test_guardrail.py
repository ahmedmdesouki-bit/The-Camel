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
from ops.kill_switch import halt, resume

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

# liquidity inputs a real live trade would carry (S6.6 live fail-closed needs these present)
LIQ = dict(bid_ask_spread_pct=0.001, avg_daily_volume=1_000_000, order_shares=1)

# ---------------- happy path ----------------
def test_clean_paper_buy_allowed(C):
    assert C.evaluate(buy(), base_state()).allow

def test_sell_to_close_allowed_without_thesis(C):
    # selling a held compliant position needs no thesis (S6.5: but it must be held)
    s = base_state(positions={"SPUS": 1000.0})
    assert C.evaluate(buy(side="sell", thesis=None), s).allow

# ---------------- S6.6: illiquidity gate fail-closed in live ----------------

def test_live_buy_without_liquidity_data_blocked(C):
    # paper skips the gate gracefully; live must FAIL CLOSED when the data is missing
    d = C.evaluate(buy(mode="live"), base_state())
    assert not d.allow and d.limit_hit == "illiquidity_data_missing"

def test_paper_buy_without_liquidity_data_allowed(C):
    # same action in paper mode still passes (graceful skip)
    assert C.evaluate(buy(mode="paper"), base_state()).allow


# ---------------- S6.5 accounting safety: phantom sells + close-only exits ----------------

def test_phantom_sell_rejected_when_nothing_held(C):
    # selling a name with no position is blocked (cannot sell what you don't hold)
    d = C.evaluate(buy(side="sell", thesis=None), base_state())
    assert not d.allow and d.limit_hit == "no_holdings"

def test_oversell_rejected(C):
    # selling more value than is held is blocked
    s = base_state(positions={"SPUS": 300.0})
    d = C.evaluate(buy(side="sell", notional_usd=500.0, thesis=None), s)
    assert not d.allow and d.limit_hit == "oversell"

def test_sell_within_holdings_allowed(C):
    s = base_state(positions={"SPUS": 1000.0})
    assert C.evaluate(buy(side="sell", notional_usd=400.0, thesis=None), s).allow

def test_frozen_name_can_be_sold_to_derisk(C):
    # close-only: a frozen holding may be SOLD (de-risk) even though it can't be bought
    s = base_state(positions={"FROZEN": 800.0})
    assert C.evaluate(buy(symbol="FROZEN", side="sell", thesis=None), s).allow

def test_frozen_name_cannot_be_bought(C):
    d = C.evaluate(buy(symbol="FROZEN"), base_state())
    assert not d.allow and d.limit_hit == "frozen"

def test_non_compliant_name_can_be_sold_to_derisk(C):
    s = base_state(positions={"BADCOMP": 800.0})
    assert C.evaluate(buy(symbol="BADCOMP", side="sell", thesis=None), s).allow

def test_non_compliant_name_cannot_be_bought(C):
    d = C.evaluate(buy(symbol="BADCOMP"), base_state())
    assert not d.allow and d.limit_hit == "not_compliant"

def test_off_whitelist_cannot_even_be_sold(C):
    # we only manage names we know — an unknown ticker is rejected on both sides
    s = base_state(positions={"TSLA": 800.0})
    d = C.evaluate(buy(symbol="TSLA", side="sell", thesis=None), s)
    assert not d.allow and d.limit_hit == "off_whitelist"


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
        "live_no_approval": (buy(mode="live", bid_ask_spread_pct=0.001,
                                  avg_daily_volume=1_000_000, order_shares=10), base_state()),
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
    assert C.evaluate(buy(mode="live", approval_id="appr_123", **LIQ), base_state()).allow

def test_phase2_auto_within_envelope(C):
    c2 = Constitution({"phase": 2, "per_order_envelope_usd": 50})
    assert c2.evaluate(buy(mode="live", notional_usd=50, **LIQ), base_state()).allow      # within envelope, no approval
    assert not c2.evaluate(buy(mode="live", notional_usd=51, **LIQ), base_state()).allow  # over envelope needs approval

def test_small_fund_no_buffer(C):
    # <1000 fund => 0% buffer, deploy freely up to position cap
    s = PortfolioState(fund_usd=500, cash_usd=120,
                       whitelist={"SPUS": Instrument("SPUS","Diversified","compliant",False,True)})
    assert C.evaluate(buy(notional_usd=100), s).allow


# ==================== S4 — HARDENING ADDITIONS ====================

# ---------------- kill switch inside evaluate ----------------
def test_kill_switch_blocks_every_action(C):
    halt()
    try:
        d = C.evaluate(buy(), base_state())
        assert not d.allow and d.limit_hit == "kill_switch"
        # blocks non-trade types too
        assert not C.evaluate(
            Action(type=ActionType.DEPLOY, business_model="halal ai tool"), base_state()
        ).allow
    finally:
        resume()

def test_resume_restores_normal_evaluation(C):
    halt(); resume()
    assert C.evaluate(buy(), base_state()).allow

# ---------------- rolling velocity stops ----------------
def test_rolling_5d_stop_rejects(C):
    d = C.evaluate(buy(), base_state(rolling_5d_pnl_pct=-0.08))
    assert not d.allow and d.limit_hit == "rolling_5d_stop"

def test_rolling_5d_stop_boundary(C):
    assert C.evaluate(buy(), base_state(rolling_5d_pnl_pct=-0.0799)).allow
    assert not C.evaluate(buy(), base_state(rolling_5d_pnl_pct=-0.08)).allow

def test_rolling_14d_stop_rejects(C):
    d = C.evaluate(buy(), base_state(rolling_14d_pnl_pct=-0.12))
    assert not d.allow and d.limit_hit == "rolling_14d_stop"

def test_rolling_14d_stop_boundary(C):
    assert C.evaluate(buy(), base_state(rolling_14d_pnl_pct=-0.1199)).allow
    assert not C.evaluate(buy(), base_state(rolling_14d_pnl_pct=-0.12)).allow

def test_cooldown_blocks_trading(C):
    d = C.evaluate(buy(), base_state(cooldown_active=True))
    assert not d.allow and d.limit_hit == "cooldown"

# ---------------- orders-per-day cap ----------------
def test_max_orders_per_day_rejects(C):
    d = C.evaluate(buy(), base_state(orders_today=10))
    assert not d.allow and d.limit_hit == "max_orders_per_day"

def test_orders_per_day_boundary(C):
    assert C.evaluate(buy(), base_state(orders_today=9)).allow
    assert not C.evaluate(buy(), base_state(orders_today=10)).allow

# ---------------- illiquidity / slippage gate ----------------
def test_wide_spread_rejects(C):
    d = C.evaluate(buy(bid_ask_spread_pct=0.0051), base_state())
    assert not d.allow and d.limit_hit == "wide_spread"

def test_spread_boundary(C):
    assert C.evaluate(buy(bid_ask_spread_pct=0.005), base_state()).allow     # exactly 0.5%
    assert not C.evaluate(buy(bid_ask_spread_pct=0.0051), base_state()).allow

def test_illiquid_order_size_rejects(C):
    # ADV 1000 shares -> 1% cap = 10 shares; 11 rejected
    d = C.evaluate(buy(avg_daily_volume=1000, order_shares=11), base_state())
    assert not d.allow and d.limit_hit == "illiquid_size"

def test_adv_participation_boundary(C):
    assert C.evaluate(buy(avg_daily_volume=1000, order_shares=10), base_state()).allow
    assert not C.evaluate(buy(avg_daily_volume=1000, order_shares=10.01), base_state()).allow

def test_illiquidity_skips_when_data_absent(C):
    # no spread / ADV on the action -> gate is skipped gracefully (IEX free tier)
    assert C.evaluate(buy(), base_state()).allow

def test_spread_skips_when_only_volume_present(C):
    # partial data: ADV present but tiny order, no spread -> allowed
    assert C.evaluate(buy(avg_daily_volume=1_000_000, order_shares=5), base_state()).allow

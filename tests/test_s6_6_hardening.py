"""
S6.6 — ops hardening: dead-man's-switch + beginner mode.
(Position accounting → test_positions.py; disk portability → test_health.py;
 illiquidity fail-closed → test_guardrail.py; prompt-injection → test_adversarial.py.)
"""
import os
import pytest

from ops.deadman import ping, PingResult
from governance.beginner_mode import beginner_limits, RailWidenedError
from guardrail.constitution import (
    Action, ActionType, Constitution, Instrument, PortfolioState, Thesis,
)


# ---------------- dead-man's-switch (network-safe stub) ----------------

def test_deadman_ping_stub_without_url(monkeypatch):
    monkeypatch.delenv("CAMEL_DEADMAN_URL", raising=False)
    r = ping()
    assert isinstance(r, PingResult)
    assert not r.sent and not r.url_configured and "stub" in r.reason

def test_deadman_ping_never_raises_on_bad_url():
    # configured but unreachable → returns a result, never raises
    r = ping(url="http://127.0.0.1:0/nope", timeout=0.2)
    assert r.url_configured and not r.sent and "failed" in r.reason


# ---------------- beginner mode (can only tighten) ----------------

def test_beginner_limits_are_tighter_than_base():
    lim = beginner_limits()
    assert lim["max_position_pct"] <= 0.20
    assert lim["daily_loss_stop_pct"] >= -0.05      # closer to zero = tighter
    assert lim["per_order_envelope_usd"] <= 50

def test_beginner_mode_rejects_a_buy_the_base_would_allow():
    # 15% position: allowed under base (20%), rejected under beginner (10%)
    wl = {"SPUS": Instrument("SPUS", "Diversified", "compliant", on_whitelist=True)}
    state = PortfolioState(fund_usd=10_000, cash_usd=9_000, whitelist=wl)
    buy = Action(type=ActionType.TRADE, symbol="SPUS", side="buy", notional_usd=1_500,
                 instrument_type="etf", thesis=Thesis("x", "y", "z"), mode="paper")
    assert Constitution().evaluate(buy, state).allow                       # base 20% ok
    d = Constitution(beginner_limits()).evaluate(buy, state)               # beginner 10%
    assert not d.allow and d.limit_hit == "max_position"

def test_beginner_profile_that_widens_is_rejected(tmp_path):
    # a hand-rolled profile that LOOSENS a rail must raise
    base = tmp_path / "base.yaml"
    bad = tmp_path / "bad.yaml"
    base.write_text("max_position_pct: 0.20\n")
    bad.write_text("max_position_pct: 0.50\n")     # wider than base → illegal
    with pytest.raises(RailWidenedError):
        beginner_limits(str(base), str(bad))

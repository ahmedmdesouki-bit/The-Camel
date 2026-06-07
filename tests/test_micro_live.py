"""
S13 — Micro-Live Readiness. Builds the live-readiness infrastructure and proves it is FAIL-SAFE:
the LiveBroker refuses by default, the readiness gate is NOT ready by default, the human approval gate
withholds by default, and the Sahm manual path moves money only on a founder-entered fill. Nothing here
puts real capital at risk — going live is a deliberate human act.
"""
import pytest

from guardrail.constitution import Action, ActionType, Decision
from ledger.writer import append_entry
from broker.positions import held_qty
from broker.live import LiveBroker, LiveTradingDisabled
from broker.manual import propose, record_fill
from governance.approval import request_approval, decide, is_approved, approval_fn
from ops.live_readiness import check_live_readiness


def _action():
    return Action(ActionType.TRADE, symbol="SPUS", side="buy", notional_usd=50, mode="live")


# ---------------- LiveBroker is gated off ----------------

def test_live_broker_refuses_by_default():
    with pytest.raises(LiveTradingDisabled):
        LiveBroker().submit(_action(), Decision(True, "ok"))                 # Phase 0


def test_live_broker_needs_all_three_switches():
    with pytest.raises(LiveTradingDisabled):
        LiveBroker(phase=1, live_enabled=False).submit(_action(), Decision(True, "ok"))
    with pytest.raises(LiveTradingDisabled):
        LiveBroker(phase=1, live_enabled=True, credentials=None).submit(_action(), Decision(True, "ok"))
    # even fully enabled it does NOT silently trade — the real integration is intentionally not wired
    with pytest.raises(NotImplementedError):
        LiveBroker(phase=1, live_enabled=True, credentials={"key": "x"}).submit(_action(), Decision(True, "ok"))


# ---------------- human approval gate (withholds by default) ----------------

def test_approval_gate_withholds_until_explicit_yes(dbs):
    request_approval(dbs, "order_42")
    assert is_approved(dbs, "order_42") is False                 # pending → not approved
    assert is_approved(dbs, "unknown_ref") is False              # missing → not approved (fail-safe)
    decide(dbs, "order_42", approve=True, decided_by="chiko")
    assert is_approved(dbs, "order_42") is True
    decide(dbs, "order_42", approve=False, decided_by="chiko")   # a later veto
    assert is_approved(dbs, "order_42") is False


def test_approval_fn_for_the_loop(dbs):
    fn = approval_fn(dbs)
    a = Action(ActionType.TRADE, symbol="HLAL", side="buy", notional_usd=50)
    a.approval_id = "appr_hlal"
    assert fn(a) is False                                        # no approval yet
    request_approval(dbs, "appr_hlal"); decide(dbs, "appr_hlal", True, "chiko")
    assert fn(a) is True


# ---------------- Sahm manual-entry path ----------------

def test_manual_propose_moves_no_money_then_records_a_fill(dbs):
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    ticket = propose(_action(), limit_price=40.0, qty=5)
    assert "Sahm" in ticket.instructions and ticket.qty == 5      # a ticket, not an execution
    assert held_qty(dbs.portfolio, "SPUS") == 0                   # proposing moved nothing

    out = record_fill(dbs, symbol="SPUS", side="buy", qty=5, price=40.0, ticket_id=ticket.ticket_id)
    assert out["cash_amount"] == -200.0 and out["position_qty"] == 5
    assert held_qty(dbs.portfolio, "SPUS") == 5                   # the founder-entered fill hit the book


# ---------------- live-readiness gate (NOT ready by default) ----------------

def test_readiness_not_ready_by_default(dbs):
    r = check_live_readiness(dbs)                                 # live_enabled defaults False
    assert r.ready is False
    assert any("explicitly enabled" in b for b in r.blockers)     # the deliberate switch is the blocker


def test_readiness_ready_only_when_every_box_passes(dbs):
    r = check_live_readiness(dbs, live_enabled=True, min_paper_runs=0)
    assert r.ready is True and r.blockers == [] and r.checks["kill_switch"] == "off"


def test_readiness_blocks_when_kill_switch_engaged(dbs):
    from ops.kill_switch import halt
    halt()
    r = check_live_readiness(dbs, live_enabled=True, min_paper_runs=0)
    assert r.ready is False and any("kill switch" in b for b in r.blockers)   # conftest resumes after

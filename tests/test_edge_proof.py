"""
S4.5 — Edge Proof v0 tests. No trade proceeds without a passing EdgeReport.
"""
import sqlite3
import pytest

from engine.edge_proof_v0 import (
    build_edge_report, compute_forward_returns, evaluate_signal, gate, log_edge_report,
)
from capital.allocator import Allocator
from guardrail.constitution import Action, ActionType, Instrument, PortfolioState, Thesis
from data.store import store_price


# ---------------- pure maths ----------------

def test_compute_forward_returns():
    assert compute_forward_returns([100, 110, 121], 1) == pytest.approx([0.10, 0.10])

def test_compute_forward_returns_horizon2():
    fr = compute_forward_returns([100, 100, 110], 2)   # only one window: 110/100-1
    assert fr == pytest.approx([0.10])


# ---------------- build_edge_report gating ----------------

def test_strong_edge_allowed():
    r = build_edge_report("SPUS", "dip", [0.05] * 30, benchmark_return=0.01)
    assert r.trade_allowed and r.sample_size == 30 and r.hit_rate == 1.0

def test_weak_evidence_rejected():
    r = build_edge_report("SPUS", "dip", [0.005] * 30, benchmark_return=0.01)  # excess negative
    assert not r.trade_allowed and "weak" in r.reason

def test_small_sample_rejected():
    r = build_edge_report("SPUS", "dip", [0.05] * 10, benchmark_return=0.01)
    assert not r.trade_allowed and "sample" in r.reason

def test_missing_benchmark_rejected():
    r = build_edge_report("SPUS", "dip", [0.05] * 30, benchmark_return=None)
    assert not r.trade_allowed and "benchmark" in r.reason

def test_stale_input_rejected():
    r = build_edge_report("SPUS", "dip", [0.05] * 30, benchmark_return=0.01, data_fresh=False)
    assert not r.trade_allowed and "stale" in r.reason

def test_no_sample_rejected():
    r = build_edge_report("SPUS", "dip", [], benchmark_return=0.01)
    assert not r.trade_allowed

def test_report_carries_distribution_stats():
    r = build_edge_report("SPUS", "dip", [0.1, -0.05, 0.2, 0.0] * 8, benchmark_return=0.0)
    assert r.worst_forward_return == pytest.approx(-0.05)
    assert r.max_drawdown <= 0.0


# ---------------- gate ----------------

def test_gate_blocks_none():
    ok, reason = gate(None)
    assert not ok and "no edge proof" in reason

def test_gate_blocks_failing_report():
    weak = build_edge_report("SPUS", "dip", [0.005] * 30, benchmark_return=0.01)
    assert not gate(weak)[0]

def test_gate_allows_passing_report():
    strong = build_edge_report("SPUS", "dip", [0.05] * 30, benchmark_return=0.01)
    assert gate(strong)[0]


# ---------------- evaluate_signal from market DB ----------------

def test_evaluate_signal_uptrend_beats_flat_benchmark(dbs):
    for i, px in enumerate([100, 101, 102, 103, 104, 105, 106, 107, 108, 109], start=1):
        store_price(dbs.market, dict(symbol="SPUS", date=f"2026-06-{i:02d}", open=px,
                    high=px, low=px, close=px, volume=1, adj_close=px), source="alpaca")
    for i in range(1, 11):
        store_price(dbs.market, dict(symbol="HLAL", date=f"2026-06-{i:02d}", open=50,
                    high=50, low=50, close=50, volume=1, adj_close=50), source="alpaca")
    r = evaluate_signal(dbs.market, "SPUS", "uptrend",
                        horizon=2, benchmark_symbol="HLAL", min_sample=3)
    assert r.sample_size >= 3 and r.trade_allowed

def test_evaluate_signal_no_data_blocked(dbs):
    r = evaluate_signal(dbs.market, "GHOST", "x", horizon=2, min_sample=3)
    assert not r.trade_allowed


# ---------------- allocator integration ----------------

def _state():
    wl = {"SPUS": Instrument("SPUS", "Diversified", "compliant", on_whitelist=True)}
    return PortfolioState(fund_usd=10_000, cash_usd=5_000, whitelist=wl)

def _buy():
    return Action(type=ActionType.TRADE, symbol="SPUS", side="buy", notional_usd=500,
                  instrument_type="etf", thesis=Thesis("x", "y", "z"), mode="paper")

def test_allocator_blocks_when_edge_required_but_absent():
    r = Allocator().request(_buy(), _state(), require_edge=True)
    assert not r.approved and r.decision.limit_hit == "no_edge_proof"

def test_allocator_blocks_failing_edge_report():
    weak = build_edge_report("SPUS", "dip", [0.005] * 30, benchmark_return=0.01)
    r = Allocator().request(_buy(), _state(), edge_report=weak)
    assert not r.approved and r.decision.limit_hit == "no_edge_proof"

def test_allocator_allows_passing_edge_report():
    strong = build_edge_report("SPUS", "dip", [0.05] * 30, benchmark_return=0.01)
    r = Allocator().request(_buy(), _state(), edge_report=strong)
    assert r.approved

def test_allocator_requires_edge_for_buys_by_default():
    # S6.5: a market buy with no EdgeReport is now blocked by default
    r = Allocator().request(_buy(), _state())
    assert not r.approved and r.decision.limit_hit == "no_edge_proof"

def test_allocator_constitution_only_when_edge_explicitly_not_required():
    # explicit override still isolates the Constitution path (pre-S6.5 behaviour)
    assert Allocator().request(_buy(), _state(), require_edge=False).approved

def test_allocator_sell_is_exempt_from_edge_requirement():
    # S6.5: reduce-only/close (sell) needs no Edge Proof — de-risking is always permitted
    wl = {"SPUS": Instrument("SPUS", "Diversified", "compliant", on_whitelist=True)}
    state = PortfolioState(fund_usd=10_000, cash_usd=5_000, whitelist=wl,
                           positions={"SPUS": 1000.0})
    sell = Action(type=ActionType.TRADE, symbol="SPUS", side="sell", notional_usd=400,
                  instrument_type="etf", mode="paper")
    assert Allocator().request(sell, state).approved   # no edge_report, default require_edge

# adversarial #9 — a strategy signal with no Edge Proof is blocked
def test_adv_signal_without_edge_proof_blocked():
    r = Allocator().request(_buy(), _state(), require_edge=True)
    assert not r.approved and r.decision.limit_hit == "no_edge_proof"


# ---------------- learning-ledger logging ----------------

def test_log_edge_report_writes_audit_row(dbs):
    r = build_edge_report("SPUS", "dip", [0.05] * 30, benchmark_return=0.01)
    log_edge_report(dbs.learning, r)
    with sqlite3.connect(dbs.learning) as conn:
        row = conn.execute(
            "SELECT decision_type, ref FROM learning_ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row[0] == "EDGE_PROOF" and row[1] == "SPUS"

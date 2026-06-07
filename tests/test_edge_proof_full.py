"""
S10 — the full 17-check Edge Proof Engine.

Locks the gating behaviour: a strong signal passes; each blocking check fails the trade; Sharia is
fail-safe (#1 in the hierarchy); the multiple-testing penalty, signal-decay test, and model-disagreement
rule all block; shadow mode logs without blocking; the DB wrapper + audit log work end-to-end.
"""
import json
from datetime import date, timedelta

from db.sqlite import connection
from data.store import store_price
from engine.edge_proof import (
    run_full_edge_proof, evaluate_signal_full, log_full_edge_report, gate,
    MIN_SAMPLE, signal_definition_hash,
)


def _strong(**over):
    """Inputs for a signal that should pass all 17 checks; override to break one."""
    kw = dict(
        symbol="AAPL", signal="quality_momentum", signal_definition="12-1 momentum, low debt",
        forward_returns=[0.05] * 60, benchmark_median_return=0.01, benchmark="SPUS",
        regime_filtered_returns=[0.05] * 25, recent_returns=[0.05] * 20,
        n_signals_tested=1, sharia_status="pass", data_quality_score=0.85, source_quorum=2,
        price=180.0, budget_usd=200.0, position_pct=0.05, mode="enforcing",
    )
    kw.update(over)
    return kw


# ---------------- the pure engine ----------------

def test_strong_signal_passes_all_blocking_checks():
    r = run_full_edge_proof(**_strong())
    assert r.would_allow and r.trade_allowed and r.reason == "edge confirmed"
    assert r.failed_checks == []
    assert r.sample_size == 60 and r.regime_filtered_sample_size == 25
    assert r.signal_definition_hash == signal_definition_hash("12-1 momentum, low debt")


def test_small_sample_blocks():
    r = run_full_edge_proof(**_strong(forward_returns=[0.05] * 10, regime_filtered_returns=[0.05] * 10))
    assert not r.trade_allowed and "sample_size" in r.failed_checks


def test_weak_excess_blocks():
    r = run_full_edge_proof(**_strong(benchmark_median_return=0.045))   # excess 0.005 < 2.5%
    assert not r.trade_allowed and "benchmark_comparison" in r.failed_checks


def test_regime_filtered_sample_blocks():
    r = run_full_edge_proof(**_strong(regime_filtered_returns=[0.05] * 5))
    assert not r.trade_allowed and "regime_filter" in r.failed_checks


def test_sharia_is_fail_safe():
    # everything else strong, but Sharia not a clear pass → blocked. Sharia is #1.
    for status in ("doubtful", "pending_review", "frozen", "unknown", "non_compliant"):
        r = run_full_edge_proof(**_strong(sharia_status=status))
        assert not r.trade_allowed and "sharia_status" in r.failed_checks


def test_signal_decay_blocks():
    # recent edge collapses to a third of the full-sample edge
    r = run_full_edge_proof(**_strong(recent_returns=[0.01] * 20))
    assert r.signal_decay_detected and not r.trade_allowed and "signal_decay" in r.failed_checks


def test_multiple_testing_penalty_blocks_marginal_edge():
    # excess 0.03 clears the base 2.5% bar but not the penalized bar after testing 20 signals
    r = run_full_edge_proof(**_strong(forward_returns=[0.04] * 60, benchmark_median_return=0.01,
                                      recent_returns=[0.04] * 20, regime_filtered_returns=[0.04] * 25,
                                      n_signals_tested=20))
    assert r.multiple_testing_penalty_applied
    assert not r.trade_allowed and "multiple_testing" in r.failed_checks


def test_worst_case_allows_only_small_position():
    big = run_full_edge_proof(**_strong(forward_returns=[0.05] * 59 + [-0.40], position_pct=0.05))
    assert "worst_case" in big.failed_checks
    small = run_full_edge_proof(**_strong(forward_returns=[0.05] * 59 + [-0.40], position_pct=0.02))
    assert "worst_case" not in small.failed_checks          # ≤2% position is allowed the deeper tail


def test_model_disagreement_routes_to_human():
    r = run_full_edge_proof(**_strong(model_votes={"bull": "buy", "bear": "sell", "sharia": "buy"}))
    assert not r.trade_allowed and "human approval" in r.reason


# ---------------- shadow vs enforcing ----------------

def test_shadow_mode_logs_but_does_not_block():
    r = run_full_edge_proof(**_strong(forward_returns=[0.05] * 10, mode="shadow"))  # would block on sample
    assert r.would_allow is False                 # the real verdict is recorded …
    assert r.trade_allowed is True                # … but shadow does not block
    allowed, reason = gate(r)
    assert allowed and "shadow" in reason and "would_block" in reason


def test_gate_enforcing_blocks_a_failing_report():
    r = run_full_edge_proof(**_strong(sharia_status="frozen"))
    allowed, reason = gate(r, enforcing=True)
    assert not allowed and "sharia_status failed" in reason


# ---------------- DB wrapper + audit log ----------------

def _seed(dbs, symbol, closes, start="2024-01-01"):
    d0 = date.fromisoformat(start)
    for k, c in enumerate(closes):
        store_price(dbs.market, {"symbol": symbol, "date": (d0 + timedelta(days=k)).isoformat(),
                                 "close": c, "adj_close": c}, source="test")


def test_evaluate_signal_full_and_log(dbs):
    _seed(dbs, "AAPL", [100.0 + k for k in range(130)])      # trending up → strong forward returns
    _seed(dbs, "SPUS", [200.0] * 130)                        # flat benchmark
    with connection(dbs.sharia) as conn:
        conn.execute("INSERT INTO sharia_status (symbol, final_status) VALUES ('AAPL','pass')")

    r = evaluate_signal_full(dbs, "AAPL", "quality_momentum", "12-1 momentum", budget_usd=500.0)
    assert r.sample_size >= MIN_SAMPLE and r.would_allow and r.trade_allowed

    log_full_edge_report(dbs, r)
    with connection(dbs.learning) as conn:
        row = dict(conn.execute("SELECT * FROM edge_reports WHERE symbol='AAPL'").fetchone())
    assert row["trade_allowed"] == 1 and row["mode"] == "enforcing"
    assert len(json.loads(row["checks_json"])) >= 17


def test_evaluate_signal_full_blocks_without_sharia_clearance(dbs):
    _seed(dbs, "ZZZ", [100.0 + k for k in range(130)])
    _seed(dbs, "SPUS", [200.0] * 130)
    r = evaluate_signal_full(dbs, "ZZZ", "mom", "def")        # no sharia_status row → 'unknown'
    assert not r.trade_allowed and "sharia_status" in r.failed_checks

"""
Enhanced operator dashboard (post-Alaa cross-build review).

Covers the new snapshot data layer and the distinctive panels — Edge-Proof decisions,
Constitution rejections-with-reasons, regime, and the live-money safety posture — plus the
read-only / offline / escaped guarantees that separate this from a browser-localStorage dash.
"""
import json

from dashboard.snapshot import build_snapshot
from dashboard.generate import build_dashboard_html
from ledger.writer import append_entry
from engine.edge_proof_v0 import EdgeReport, log_edge_report
from sharia.whitelist import add_instrument


# ---------------- snapshot data layer ----------------

def test_snapshot_is_json_serializable_and_has_sections(dbs):
    snap = build_snapshot(dbs, mode="paper")
    json.dumps(snap)  # must not raise
    for key in ("mode", "health", "kpis", "governance", "positions", "ledger",
                "runs", "guardrail", "edge_decisions", "regime", "whitelist"):
        assert key in snap
    assert snap["mode"] == "paper"
    assert snap["governance"]["live_at_risk"] == 0.0          # paper only, always $0


def test_snapshot_kpis_and_cash_drag(dbs):
    append_entry(dbs.portfolio, "DEPOSIT", "", 100.0)
    snap = build_snapshot(dbs, mode="paper")
    assert snap["kpis"]["cash"] == 100.0
    # all cash, no positions → 100% cash drag
    assert snap["kpis"]["cash_drag_pct"] == 100.0


def test_governance_posture_is_honest_booleans(dbs):
    g = build_snapshot(dbs, mode="paper")["governance"]
    assert g["phase"] == 0 and "paper" in g["phase_label"].lower()
    assert g["gate_total"] == len(g["gate_items"])
    # phase-0 + leverage-off + approval-required should all be satisfied on a fresh repo
    labels = {it["label"]: it["ok"] for it in g["gate_items"]}
    assert any("paper only" in k and v for k, v in labels.items())
    assert any("Leverage disabled" in k and v for k, v in labels.items())


# ---------------- Edge-Proof decisions panel ----------------

def test_edge_proof_decision_surfaces_with_reason(dbs):
    blocked = EdgeReport(
        symbol="NVDA", signal="momentum_12_1", sample_size=8, hit_rate=0.4,
        median_forward_return=-0.01, worst_forward_return=-0.2, max_drawdown=-0.2,
        benchmark="SPUS", benchmark_excess_return=-0.02, confidence=0.3,
        trade_allowed=False, reason="sample too small (8 < 50)")
    log_edge_report(dbs.learning, blocked)

    snap = build_snapshot(dbs, mode="paper")
    assert len(snap["edge_decisions"]) == 1
    d = snap["edge_decisions"][0]
    assert d["symbol"] == "NVDA" and d["trade_allowed"] is False
    assert "sample too small" in d["reason"]

    h = build_dashboard_html(dbs, mode="paper")
    assert "Edge-Proof decisions" in h
    assert "BLOCKED" in h and "sample too small (8 &lt; 50)" in h   # reason rendered + escaped


def test_dashboard_has_decision_and_regime_panels(dbs):
    h = build_dashboard_html(dbs, mode="paper")
    # the panels that make ours different from a portfolio tracker
    assert "Edge-Proof decisions" in h
    assert "Macro regime" in h
    assert "safety posture" in h
    assert "Live capital at risk" in h


# ---------------- read-only / offline / safe guarantees ----------------

def test_dashboard_is_offline_and_read_only(dbs):
    h = build_dashboard_html(dbs, mode="paper")
    # no live fetch, no client source-of-truth, no order entry, no script injection surface
    assert "<script" not in h.lower()
    assert "fetch(" not in h and "localStorage" not in h
    assert "<form" not in h.lower() and "<input type='text'" not in h
    assert "no order entry" in h


def test_dashboard_escapes_hostile_symbol_in_new_panels(dbs):
    add_instrument(dbs.sharia, "<img src=x onerror=alert(1)>", "etf", approved_by="x", scan_id="s9")
    h = build_dashboard_html(dbs, mode="paper")
    assert "<img src=x" not in h
    assert "&lt;img src=x" in h

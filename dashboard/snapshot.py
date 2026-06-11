"""
Dashboard snapshot builder (S6 → enhanced after the Alaa cross-build review).

Pure data layer for the operator dashboard: reads the seven SQLite DBs and the founder-owned
limits, and returns one JSON-serializable dict describing the Camel's current state. The HTML
renderer (`dashboard/generate.py`) turns this into a static, read-only page — there is NO live
web fetch, NO server, and NO client-side source of truth (unlike a browser-localStorage dash).
That keeps the operator view deterministic, offline, and testable.

The snapshot deliberately surfaces what makes The Camel different from a portfolio tracker:
the **decisions** — Edge-Proof verdicts and Constitution rejections-with-reasons — plus the
**regime** and the **live-money safety posture**, not just holdings.
"""
from __future__ import annotations

import json
import os
from typing import List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from ops.health_monitor import check
from ops.kill_switch import is_halted

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LIMITS_PATH = os.path.join(_ROOT, "config", "limits.yaml")

_PHASE_LABELS = {0: "Phase 0 · paper only", 1: "Phase 1 · micro-live",
                 2: "Phase 2 · auto", 3: "Phase 3 · scale"}


def _rows(db_path: str, sql: str) -> List[dict]:
    try:
        with connection(db_path) as conn:
            return [dict(r) for r in conn.execute(sql).fetchall()]
    except Exception:
        return []


def _round(v, n: int = 2):
    try:
        return round(float(v), n)
    except (TypeError, ValueError):
        return v


def _load_limits() -> dict:
    try:
        import yaml
        with open(_LIMITS_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _edge_decisions(learning_db: str, limit: int = 12) -> List[dict]:
    """Pull Edge-Proof verdicts out of the learning ledger audit trail."""
    out: List[dict] = []
    rows = _rows(learning_db,
                 "SELECT ts, thesis_summary, expected_outcome, ref FROM learning_ledger "
                 "WHERE decision_type='EDGE_PROOF' ORDER BY id DESC LIMIT %d" % int(limit))
    for r in rows:
        report = {}
        try:
            report = json.loads(r.get("expected_outcome") or "{}")
        except (ValueError, TypeError):
            report = {}
        out.append({
            "ts": r.get("ts"),
            "symbol": report.get("symbol") or r.get("ref"),
            "signal": report.get("signal"),
            "trade_allowed": bool(report.get("trade_allowed")),
            "reason": report.get("reason") or "",
            "sample_size": report.get("sample_size"),
            "hit_rate": _round(report.get("hit_rate"), 3),
            "median_forward_return": _round(report.get("median_forward_return"), 4),
            "benchmark_excess_return": _round(report.get("benchmark_excess_return"), 4),
            "confidence": _round(report.get("confidence"), 2),
        })
    return out


def _governance(dbs: CamelDbs, mode: str, cash: float, positions_value: float) -> dict:
    limits = _load_limits()
    phase = int(limits.get("phase", 0) or 0)
    halted = is_halted()
    allow_leverage = bool(limits.get("allow_leverage", False))
    require_approval_live = bool(limits.get("require_approval_live", True))

    # An HONEST safety posture (not a fabricated "X/10"): each item is a real boolean fact.
    items = [
        {"label": "Phase 0 — paper only (no live capital)", "ok": phase == 0},
        {"label": "Leverage disabled", "ok": not allow_leverage},
        {"label": "Live trades require human approval", "ok": require_approval_live},
        {"label": "Kill switch off (not halted)", "ok": not halted},
        {"label": "Per-order envelope set", "ok": bool(limits.get("per_order_envelope_usd"))},
        {"label": "Daily loss-stop configured", "ok": limits.get("daily_loss_stop_pct") is not None},
    ]
    passed = sum(1 for it in items if it["ok"])
    return {
        "phase": phase,
        "phase_label": _PHASE_LABELS.get(phase, f"Phase {phase}"),
        "kill_switch": "HALTED" if halted else "off",
        "allow_leverage": allow_leverage,
        "require_approval_live": require_approval_live,
        "live_at_risk": 0.0,                      # paper only; always $0 until a live phase flag
        "paper_at_risk": _round(positions_value),
        "gate_items": items,
        "gate_passed": passed,
        "gate_total": len(items),
    }


def _desks(dbs: CamelDbs) -> List[dict]:
    """S17.7 — the workforce's current desk status (latest run per desk + pause state), for the Kitchen."""
    try:
        from research.workforce import latest_desk_status
        from governance.desk_control import all_control
        status = latest_desk_status(dbs)
        paused = all_control(dbs)
        return [{"desk_id": k, "status": v["status"], "summary": v["summary"], "ts": v["ts"],
                 "evidence_n": v["evidence_n"], "paused": paused.get(k, False)}
                for k, v in status.items()]
    except Exception:
        return []


def _board(dbs: CamelDbs) -> List[dict]:
    """S17.7 — the live Opportunity Board (proposed rows, founder-ordered), for the Kitchen."""
    try:
        from loop.opportunity_board import current_board
        out: List[dict] = []
        for r in current_board(dbs):
            try:
                reasons = json.loads(r.get("reason_chain") or "[]")
            except (ValueError, TypeError):
                reasons = []
            out.append({
                "id": r.get("id"), "symbol": r.get("symbol"), "action": r.get("action"),
                "score": _round(r.get("score"), 3), "regime": r.get("regime"),
                "sharia_status": r.get("sharia_status"), "edge_allowed": bool(r.get("edge_allowed")),
                "hit_rate": _round(r.get("hit_rate"), 3), "confidence": _round(r.get("confidence"), 2),
                "recommended_action": r.get("recommended_action"),
                "invalidation": r.get("invalidation"), "reason_chain": reasons,
            })
        return out
    except Exception:
        return []


def _strategies() -> List[dict]:
    """The strategy roster + fit metadata (the S11 registry/matrix surfaced read-only for the founder).
    Reflects the BUILT strategies and their promotion rung — not live positions. A new strategy ships
    un-promoted and earns its rung via the Edge Lab."""
    try:
        from trader.strategies.core_dca import CoreDCA
        from trader.strategies.quality_momentum import QualityMomentum
        from trader.strategies.dividend_growth import DividendGrowth
        from trader.strategies.etf_rotation import ETFRegimeRotation
        from trader.strategies.momentum import TimeSeriesMomentum
        from trader.strategies.mean_reversion import MeanReversion
        from trader.strategies.dca_ladder import DCALadder
        roster = [CoreDCA(), QualityMomentum(), DividendGrowth(), ETFRegimeRotation(),
                  TimeSeriesMomentum(), MeanReversion(), DCALadder()]
        out: List[dict] = []
        for st in roster:
            m = st.meta
            out.append({
                "id": m.id, "name": m.name, "family": m.thesis_family,
                "status": getattr(m.status, "value", str(m.status)),
                "rung": getattr(m.mode, "value", str(m.mode)),
                "regimes": ", ".join(m.applicable_regimes) if m.applicable_regimes else "all",
                "max_position_pct": _round(m.max_single_position * 100, 1),
                "base_rate": _round(m.base_rate, 2),
            })
        return out
    except Exception:
        return []


def build_snapshot(dbs: CamelDbs, mode: str = "paper") -> dict:
    """Return a JSON-serializable snapshot of the Camel's current governed state."""
    report = check(dbs, mode=mode)

    positions = _rows(dbs.portfolio,
                      "SELECT symbol, qty, avg_cost, market_price, market_value, "
                      "unrealized_pnl, realized_pnl, status FROM positions ORDER BY symbol")
    ledger = _rows(dbs.portfolio,
                   "SELECT ts, type, symbol, amount, balance_after, ref "
                   "FROM ledger ORDER BY id DESC LIMIT 20")
    runs = _rows(dbs.portfolio,
                 "SELECT id, started_at, ended_at, phase, outcome FROM runs ORDER BY id DESC LIMIT 12")
    guardrail = _rows(dbs.portfolio,
                      "SELECT ts, decision, reason, limit_hit, action_json "
                      "FROM guardrail_events ORDER BY id DESC LIMIT 20")
    whitelist = _rows(dbs.sharia,
                      "SELECT symbol, sharia_status, frozen FROM whitelist ORDER BY symbol")
    regime_hist = _rows(dbs.macro,
                        "SELECT classified_at, regime, confidence, signals FROM regime_history "
                        "ORDER BY id DESC LIMIT 10")
    edge = _edge_decisions(dbs.learning)

    # ---- derived KPIs ----
    cash = ledger[0]["balance_after"] if ledger else 0.0
    positions_value = sum(float(p.get("market_value") or 0) for p in positions)
    total_value = positions_value + float(cash or 0)
    unrealized = sum(float(p.get("unrealized_pnl") or 0) for p in positions)
    realized = sum(float(p.get("realized_pnl") or 0) for p in positions)
    cash_drag = (float(cash or 0) / total_value * 100) if total_value > 0 else 0.0
    open_positions = [p for p in positions if (p.get("status") or "open") == "open"]

    # ---- guardrail rejections-with-reasons (decision == 0 → blocked) ----
    rejections = []
    for g in guardrail:
        sym = ""
        try:
            sym = (json.loads(g.get("action_json") or "{}") or {}).get("symbol", "")
        except (ValueError, TypeError):
            sym = ""
        rejections.append({
            "ts": g.get("ts"),
            "blocked": int(g.get("decision") or 0) == 0,
            "symbol": sym,
            "reason": g.get("reason") or "",
            "limit_hit": g.get("limit_hit") or "",
        })

    latest_regime = None
    if regime_hist:
        r0 = regime_hist[0]
        try:
            sigs = json.loads(r0.get("signals") or "[]")
        except (ValueError, TypeError):
            sigs = []
        latest_regime = {
            "classified_at": r0.get("classified_at"),
            "regime": r0.get("regime"),
            "confidence": _round(r0.get("confidence"), 2),
            "signals": sigs,
        }

    return {
        "mode": mode,
        "health": {"status": report.status, "issues": list(report.issues), "checks": dict(report.checks)},
        "kpis": {
            "cash": _round(cash),
            "positions_value": _round(positions_value),
            "total_value": _round(total_value),
            "unrealized_pnl": _round(unrealized),
            "realized_pnl": _round(realized),
            "cash_drag_pct": _round(cash_drag, 1),
            "open_positions": len(open_positions),
        },
        "governance": _governance(dbs, mode, cash=float(cash or 0), positions_value=positions_value),
        "positions": [{
            "symbol": p.get("symbol"), "qty": p.get("qty"), "avg_cost": _round(p.get("avg_cost")),
            "market_price": _round(p.get("market_price")), "market_value": _round(p.get("market_value")),
            "unrealized_pnl": _round(p.get("unrealized_pnl")), "realized_pnl": _round(p.get("realized_pnl")),
            "status": p.get("status") or "open",
        } for p in positions],
        "ledger": [{
            "ts": l.get("ts"), "type": l.get("type"), "symbol": l.get("symbol"),
            "amount": _round(l.get("amount")), "balance_after": _round(l.get("balance_after")),
        } for l in ledger],
        "runs": runs,
        "guardrail": rejections,
        "edge_decisions": edge,
        "regime": latest_regime,
        "regime_history": [{
            "classified_at": r.get("classified_at"), "regime": r.get("regime"),
            "confidence": _round(r.get("confidence"), 2),
        } for r in regime_hist],
        "whitelist": [{
            "symbol": w.get("symbol"), "sharia_status": w.get("sharia_status"),
            "frozen": bool(w.get("frozen")),
        } for w in whitelist],
        "desks": _desks(dbs),                  # S17.7 — the Kitchen: workforce status
        "board": _board(dbs),                  # S17.7 — the Kitchen: Opportunity Board
        "strategies": _strategies(),           # S17 — the strategy roster + fit metadata (read-only)
    }

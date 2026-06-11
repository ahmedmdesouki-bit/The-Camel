"""
S17.5 — memory consolidation (Level 3): roll the workforce's operational memory into a compact, persisted
summary + detected patterns the Supervisor and the founder can act on.

Two streams, both read-only aggregation (no learning *applied* here — propose-only stays propose-only):
  * DESK RELIABILITY — per-desk run counts, error rate, last status, evidence produced (from `desk_runs`).
  * STRATEGY SCORES — a best-effort base-rate snapshot (from `strategy_base_rates` if present).

`detect_patterns` then flags the things worth a human's eye — an unreliable desk, an underperforming
strategy — and the whole summary is appended to `memory_consolidation` (append-only history). Pure +
deterministic; persists a digest, never edits a rule, a weight, or the Constitution.
"""
from __future__ import annotations

import json
from typing import Dict, List

from db.paths import CamelDbs
from db.sqlite import connection

UNRELIABLE_DESK_ERROR_RATE = 0.30
UNDERPERFORM_BASE_RATE = 0.45
MIN_RUNS_TO_JUDGE = 3
MIN_N_TO_JUDGE = 20


def consolidate_desk_reliability(dbs: CamelDbs) -> Dict[str, dict]:
    """Per-desk reliability from the `desk_runs` audit trail."""
    from research.workforce import _ensure_desk_runs
    _ensure_desk_runs(dbs.learning)
    with connection(dbs.learning) as conn:
        rows = conn.execute("SELECT desk_id, status, evidence_n, ts FROM desk_runs ORDER BY id").fetchall()
    out: Dict[str, dict] = {}
    for r in rows:
        d = out.setdefault(r["desk_id"], {"runs": 0, "errors": 0, "ok": 0, "empty": 0, "paused": 0,
                                          "evidence_total": 0, "last_status": None, "last_ts": None})
        d["runs"] += 1
        st = r["status"]
        if st == "error":
            d["errors"] += 1
        elif st in ("ok", "empty", "paused"):
            d[st] += 1
        d["evidence_total"] += int(r["evidence_n"] or 0)
        d["last_status"], d["last_ts"] = st, r["ts"]
    for d in out.values():
        d["error_rate"] = round(d["errors"] / d["runs"], 4) if d["runs"] else 0.0
    return out


def consolidate_strategy_scores(dbs: CamelDbs) -> Dict[str, dict]:
    """Best-effort per-strategy base-rate snapshot (empty if `strategy_base_rates` is absent)."""
    try:
        with connection(dbs.learning) as conn:
            rows = conn.execute("SELECT strategy_id, base_rate, n FROM strategy_base_rates").fetchall()
        return {r["strategy_id"]: {"base_rate": r["base_rate"], "n": r["n"]} for r in rows}
    except Exception:
        return {}


def detect_patterns(desks: Dict[str, dict], strategies: Dict[str, dict]) -> List[dict]:
    """Flag what deserves a human's eye — judged only once there is enough evidence to be fair."""
    patterns: List[dict] = []
    for did, d in sorted(desks.items()):
        if d["runs"] >= MIN_RUNS_TO_JUDGE and d["error_rate"] > UNRELIABLE_DESK_ERROR_RATE:
            patterns.append({"kind": "unreliable_desk", "subject": did,
                             "detail": f"error_rate {d['error_rate']:.0%} over {d['runs']} runs"})
    for sid, s in sorted(strategies.items()):
        n = int(s.get("n") or 0)
        br = float(s.get("base_rate") or 0.0)
        if n >= MIN_N_TO_JUDGE and br < UNDERPERFORM_BASE_RATE:
            patterns.append({"kind": "underperforming_strategy", "subject": sid,
                             "detail": f"base_rate {br:.2f} (n={n})"})
    return patterns


def _persist(dbs: CamelDbs, summary: dict) -> None:
    from db.learning import init_learning_db
    init_learning_db(dbs.learning)            # single source of truth is db/learning.py
    with connection(dbs.learning) as conn:
        conn.execute("INSERT INTO memory_consolidation (summary) VALUES (?)", (json.dumps(summary),))


def consolidate(dbs: CamelDbs, *, persist: bool = True) -> dict:
    """Build (and optionally persist) the consolidated operational memory + detected patterns."""
    desks = consolidate_desk_reliability(dbs)
    strategies = consolidate_strategy_scores(dbs)
    summary = {"desks": desks, "strategies": strategies,
               "patterns": detect_patterns(desks, strategies)}
    if persist:
        _persist(dbs, summary)
    return summary

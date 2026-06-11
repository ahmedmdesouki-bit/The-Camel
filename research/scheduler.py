"""
S17.3 — the scheduler/DAG: desks feed each other, so run them in dependency order and DON'T run a desk on
the output of an upstream that failed.

The S17.1 Workforce runs desks in a fixed list. This adds the dependency graph the desks actually form:
SCOUT pulls data; the evidence desks (HERALD/ORACLE/MUFTI/QUANT) read that data; STEWARD reads the book;
CONDUCTOR synthesizes everything. If SCOUT errors, running QUANT on stale/empty data is worse than not
running it — so a desk whose upstream ended 'error' or 'skipped' is itself SKIPPED (recorded, not run).

`topological_order` is deterministic (alphabetical within a rank) and raises on a cycle. Pure orchestration
over Workforce.run_desk — no new path to act or move money.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from db.paths import CamelDbs

# The 7-desk roster's real dependency graph (desk_id -> upstream desk_ids it consumes).
DEFAULT_DAG: Dict[str, List[str]] = {
    "scout": [],                                              # pulls data — the root
    "steward": [],                                            # reads the existing book — independent
    "herald": ["scout"],
    "oracle": ["scout"],
    "mufti": ["scout"],
    "quant": ["scout"],
    "conductor": ["herald", "oracle", "mufti", "quant", "steward"],
}


def topological_order(deps: Dict[str, List[str]]) -> List[str]:
    """Deterministic topological order (alphabetical within a rank). Raises ValueError on a cycle."""
    remaining = {k: set(v) for k, v in deps.items()}
    for ups in list(remaining.values()):                     # nodes referenced only as an upstream
        for u in ups:
            remaining.setdefault(u, set())
    order: List[str] = []
    while remaining:
        ready = sorted(k for k, ups in remaining.items() if not (ups & set(remaining)))
        if not ready:
            raise ValueError(f"cycle in DAG among {sorted(remaining)}")
        for k in ready:
            order.append(k)
            remaining.pop(k)
    return order


def run_dag(workforce, dbs: CamelDbs, deps: Dict[str, List[str]] = None,
            ctx: Optional[Dict] = None, *, skip_on_upstream_failure: bool = True) -> list:
    """Run the workforce in dependency order. A desk whose upstream ended error/skipped is SKIPPED
    (recorded), not run. Returns the DeskResults in execution order."""
    from research.workforce import DeskResult, record_desk_run, _utcnow
    deps = deps if deps is not None else DEFAULT_DAG
    status: Dict[str, str] = {}
    out = []
    for did in topological_order(deps):
        bad = [u for u in deps.get(did, []) if status.get(u) in ("error", "skipped")]
        if skip_on_upstream_failure and bad:
            r = DeskResult(did, "skipped", summary=f"upstream failed: {bad}",
                           started_at=_utcnow(), ended_at=_utcnow())
            record_desk_run(dbs, r)
        else:
            r = workforce.run_desk(dbs, did, ctx)
        status[did] = r.status
        out.append(r)
    return out

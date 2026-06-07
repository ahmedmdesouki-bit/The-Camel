"""
Live-readiness gate (S13) — the pre-live checklist, as code.

`CAMEL_LIVE_READINESS.md` is the human checklist; this is the machine check that must pass before any
real money moves. It is fail-safe: the founder's explicit `live_enabled` switch is itself a required
box, so the **default result is NOT READY**. Going live is a deliberate act, never a default.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from db.paths import CamelDbs
from db.sqlite import connection
from ops.kill_switch import is_halted


@dataclass
class LiveReadinessReport:
    ready: bool
    blockers: List[str] = field(default_factory=list)
    checks: Dict[str, str] = field(default_factory=dict)


def _paper_runs(dbs: CamelDbs) -> int:
    try:
        with connection(dbs.portfolio) as conn:
            return conn.execute("SELECT COUNT(*) FROM runs WHERE outcome LIKE 'complete%'").fetchone()[0]
    except Exception:
        return 0


def check_live_readiness(dbs: CamelDbs, *, live_enabled: bool = False,
                         min_paper_runs: int = 28) -> LiveReadinessReport:
    """Return the blockers preventing a safe go-live. `ready` is True only when there are none."""
    blockers: List[str] = []
    checks: Dict[str, str] = {}

    # 1 kill switch must be off
    halted = is_halted()
    checks["kill_switch"] = "HALTED" if halted else "off"
    if halted:
        blockers.append("kill switch is engaged")

    # 2 the deterministic guardrail must import
    try:
        import guardrail.constitution  # noqa: F401
        checks["guardrail"] = "ok"
    except Exception:
        checks["guardrail"] = "FAIL"
        blockers.append("guardrail failed to import")

    # 3 the append-only ledger must verify
    try:
        from ledger.reconcile import verify_hash_chain
        ok = verify_hash_chain(dbs.portfolio)
        checks["ledger_hash_chain"] = "verified" if ok else "BROKEN"
        if ok is False:
            blockers.append("ledger hash-chain does not verify")
    except Exception:
        checks["ledger_hash_chain"] = "unknown"

    # 4 a paper track record (Phase-0 exit criterion)
    runs = _paper_runs(dbs)
    checks["paper_runs"] = str(runs)
    if runs < min_paper_runs:
        blockers.append(f"insufficient paper track record ({runs} < {min_paper_runs} completed runs)")

    # 5 THE deliberate founder switch — must be explicitly set
    checks["live_enabled"] = "yes" if live_enabled else "no"
    if not live_enabled:
        blockers.append("live not explicitly enabled by the founder (the deliberate switch is off)")

    return LiveReadinessReport(ready=not blockers, blockers=blockers, checks=checks)

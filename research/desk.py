"""
Research Desk (S12.5) — the per-vertical analyst framework. Designed now, DORMANT by default.

The orchestrator's master switch defaults **OFF** — the desk stays dark until capital + a proven edge
justify the token spend. When on, each vertical `AnalystDesk` reads the governed DBs and writes
**EvidenceObjects** to `research_evidence` (and nowhere else). Critically, a desk has **no execute path
at all** — the base class exposes only `analyze`; there is no method that could place a trade. Evidence
feeds Edge Proof; it never bypasses a gate. The learning loop is narrow + safe (a desk may refine
retrieval/priors, never the Constitution).

When the real Claude-Agent-SDK desks land, they implement `analyze` and return the same EvidenceObjects;
the framework, contract, switch, and audit trail are already here and unchanged.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from research.evidence import EvidenceObject


class AnalystDesk:
    """A vertical research desk. Subclasses set `desk_id` and implement `analyze`. EVIDENCE ONLY —
    there is deliberately no `act`/`execute`/`trade` method anywhere on this class."""
    desk_id: str = "base"

    def analyze(self, dbs: CamelDbs, context: Optional[Dict] = None) -> List[EvidenceObject]:  # pragma: no cover
        raise NotImplementedError


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_evidence(dbs: CamelDbs, ev: EvidenceObject) -> Optional[int]:
    """Persist one validated EvidenceObject. Invalid notes are refused (returns None)."""
    if not ev.valid():
        return None
    with connection(dbs.learning) as conn:
        cur = conn.execute(
            "INSERT INTO research_evidence (desk, claim, scope, evidence_ids, source_count, freshness, "
            " disagreement_score, confidence, horizon, direction, invalidation_conditions, "
            " recommended_action, portfolio_fit, compliance_status, known_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ev.desk, ev.claim, ev.scope, json.dumps(ev.evidence_ids), ev.source_count, ev.freshness,
             ev.disagreement_score, ev.confidence, ev.horizon, ev.direction, ev.invalidation_conditions,
             ev.recommended_action, ev.portfolio_fit, ev.compliance_status, ev.known_at or _utcnow()),
        )
        return cur.lastrowid


class ResearchDesk:
    """Orchestrates the vertical desks behind a master switch + a token budget."""

    def __init__(self, *, enabled: bool = False, token_budget: int = 0):
        self.enabled = enabled               # MASTER SWITCH — defaults OFF (dormant)
        self.token_budget = token_budget
        self._desks: List[AnalystDesk] = []

    def register(self, desk: AnalystDesk) -> None:
        self._desks.append(desk)

    @property
    def desks(self) -> List[str]:
        return [d.desk_id for d in self._desks]

    def run(self, dbs: CamelDbs, context: Optional[Dict] = None, *, cost_per_desk: int = 1) -> List[EvidenceObject]:
        """Run every desk IF the master switch is on and budget remains; persist valid evidence; return it.
        Returns [] (and writes nothing) when dormant — the safe default."""
        if not self.enabled:
            return []
        out: List[EvidenceObject] = []
        budget = self.token_budget
        for desk in self._desks:
            if budget < cost_per_desk:
                break
            budget -= cost_per_desk
            for ev in desk.analyze(dbs, context):
                if ev.valid():
                    write_evidence(dbs, ev)
                    out.append(ev)
        return out

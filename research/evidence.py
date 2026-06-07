"""
Evidence-object contract (S12.5) — a research note is a mini credit-memo, not a chat reply.

Every analyst desk emits structured EvidenceObjects against this 13-field contract; that object — not
free text — is what flows into Edge Proof. Validation is strict: a malformed note is rejected, never
stored. The `recommended_action` is a PROPOSAL only; nothing here can place a trade.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

_DIRECTIONS = {"positive", "negative", "neutral"}


@dataclass
class EvidenceObject:
    desk: str
    claim: str
    scope: str
    evidence_ids: List[str] = field(default_factory=list)
    source_count: int = 0
    freshness: str = ""
    disagreement_score: float = 0.0
    confidence: float = 0.0
    horizon: str = ""
    direction: str = "neutral"
    invalidation_conditions: str = ""
    recommended_action: str = "none"      # a proposal — never executed
    portfolio_fit: str = ""
    compliance_status: str = "unknown"
    known_at: Optional[str] = None

    def errors(self) -> List[str]:
        e: List[str] = []
        if not self.claim:
            e.append("missing claim")
        if not self.scope:
            e.append("missing scope")
        if not (0.0 <= self.confidence <= 1.0):
            e.append("confidence out of [0,1]")
        if self.direction not in _DIRECTIONS:
            e.append(f"direction must be one of {sorted(_DIRECTIONS)}")
        if self.source_count < 1:
            e.append("source_count < 1 (a claim needs at least one source)")
        return e

    def valid(self) -> bool:
        return not self.errors()

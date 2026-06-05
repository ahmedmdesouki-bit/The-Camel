"""
Data quality scoring (S4 v1; refined in S7).

Combines source count, freshness, cross-source agreement, and source reputation into a
single `quality_score` and a hard `decision_eligible` flag. Data that is stale, single-source
when a quorum is required, or from an unapproved source is NOT eligible to drive a decision.
"""
from __future__ import annotations
from dataclasses import dataclass

MIN_AGREEMENT = 0.99       # multi-source close prices must agree within 1%
QUORUM_SOURCES = 2         # important signals want >= 2 sources


@dataclass
class QualityScore:
    quality_score: float
    decision_eligible: bool
    reason: str


def score(
    source_count: int,
    freshness_hours: float,
    source_agreement: float,
    source_reputation: str,
    max_age_hours: float = 24.0,
    require_quorum: bool = False,
) -> QualityScore:
    """
    source_agreement: 1.0 = identical across sources (use 1.0 for a single source).
    source_reputation: 'approved' | 'unknown' | 'rejected'.
    """
    reasons = []
    eligible = True

    if source_count < 1:
        return QualityScore(0.0, False, "no sources")
    if source_reputation == "rejected":
        return QualityScore(0.0, False, "source reputation rejected")
    if freshness_hours > max_age_hours:
        eligible = False
        reasons.append(f"stale ({freshness_hours:.1f}h)")
    if require_quorum and source_count < QUORUM_SOURCES:
        eligible = False
        reasons.append("below source quorum")
    if source_count >= 2 and source_agreement < MIN_AGREEMENT:
        eligible = False
        reasons.append(f"sources disagree ({source_agreement:.3f})")
    if source_reputation != "approved":
        reasons.append("source not on approved allowlist")

    # Simple 0..1 score: penalise staleness, disagreement, thin sourcing, low reputation.
    freshness_factor = max(0.0, 1.0 - freshness_hours / max_age_hours) if max_age_hours else 0.0
    source_factor = min(1.0, source_count / QUORUM_SOURCES)
    rep_factor = {"approved": 1.0, "unknown": 0.6, "rejected": 0.0}.get(source_reputation, 0.5)
    agree_factor = source_agreement if source_count >= 2 else 1.0
    quality = round(0.30 * freshness_factor + 0.25 * source_factor
                    + 0.20 * rep_factor + 0.25 * agree_factor, 3)

    return QualityScore(quality, eligible, "; ".join(reasons) or "ok")

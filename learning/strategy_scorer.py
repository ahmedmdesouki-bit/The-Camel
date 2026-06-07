"""
L2 — strategy scorer (S11). Auto: nudge a strategy's blend weight, but ONLY within a founder-set band.

Realized-vs-expected score → a small weight step, clamped to the band. This tier can re-weight; it can
never activate/deactivate a strategy (that's L3 propose-only) or change the band itself (L4 founder-only).
"""
from __future__ import annotations

from typing import Tuple


def score_vs_expected(realized: float, expected: float) -> float:
    """>1 beat expectations, <1 missed. Guarded for a zero/negative expectation."""
    if expected <= 0:
        return 1.0 if realized >= expected else 0.5
    return round(realized / expected, 3)


def auto_weight(current_weight: float, score: float, band: Tuple[float, float],
                step: float = 0.05) -> float:
    """Move the weight one step toward more (score>1) or less (score<1), clamped to the band."""
    lo, hi = band
    direction = 1 if score > 1.0 else (-1 if score < 1.0 else 0)
    return round(max(lo, min(hi, current_weight + direction * step)), 4)

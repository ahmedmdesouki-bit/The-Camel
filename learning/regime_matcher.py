"""
Regime→strategy affinity (S11). Learn which regimes a strategy works in — but only with enough evidence.

Affinity for a regime is emitted only at N ≥ 20 resolved outcomes (the reviewer-set minimum); below that
the sample is too thin to trust. Pure. Feeds L3 proposals (propose-only), never an automatic rule change.
"""
from __future__ import annotations

from typing import Dict, List

MIN_SAMPLES_PER_REGIME = 20


def learn_affinity(outcomes_by_regime: Dict[str, List[bool]]) -> Dict[str, float]:
    """{regime: [True/False resolved-trade wins]} → {regime: win_rate} for regimes with N ≥ 20 only."""
    out: Dict[str, float] = {}
    for regime, wins in outcomes_by_regime.items():
        if len(wins) >= MIN_SAMPLES_PER_REGIME:
            out[regime] = round(sum(1 for w in wins if w) / len(wins), 3)
    return out

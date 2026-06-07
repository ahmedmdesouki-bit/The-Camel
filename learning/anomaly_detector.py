"""
Anomaly detector (S11). Flag a strategy whose realized hit-rate is materially below its base-rate.

Conservative: needs a minimum sample before flagging (no crying wolf on noise). A flag does not kill the
strategy — it feeds an L3 proposal (e.g., demote to cooldown / pause) for founder review.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_SAMPLE = 20
DEFAULT_GAP = 0.15            # realized ≥ 15pp below base-rate → anomalous


@dataclass
class AnomalyFlag:
    flagged: bool
    realized_hit_rate: float
    base_rate: float
    gap: float
    note: str = ""


def detect_underperformance(realized_hit_rate: float, base_rate: float, n: int,
                            gap_threshold: float = DEFAULT_GAP) -> AnomalyFlag:
    gap = round(base_rate - realized_hit_rate, 4)
    flagged = n >= MIN_SAMPLE and gap >= gap_threshold
    note = (f"realized {realized_hit_rate:.0%} is {gap:.0%} below base-rate {base_rate:.0%} over {n}"
            if flagged else "within tolerance" if n >= MIN_SAMPLE else f"sample too small ({n} < {MIN_SAMPLE})")
    return AnomalyFlag(flagged, realized_hit_rate, base_rate, gap, note)

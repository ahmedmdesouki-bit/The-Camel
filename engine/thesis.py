"""
Thesis and base-rate card — v11 §5 "fill before acting on any signal".

A position CANNOT be proposed without a complete ThesisCard (invalidation +
profit_take + time_stop all non-empty). This enforces the CLAUDE.md rule:
"No position without a written invalidation point."
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BaseRateCard:
    """v11 Base-Rate Worksheet — attach to every thesis."""
    signal: str = ""
    comparables_n: int = 0          # sample size; N < 10 = low trust
    horizon: str = ""               # e.g. "3–6 months"
    hit_rate: float = 0.0           # fraction, e.g. 0.62
    median_magnitude: str = ""      # e.g. "+12%"
    already_priced_in: str = ""
    counter_signals: List[str] = field(default_factory=list)
    overfitting_check: str = ""
    probability_tilt: str = ""
    position_size_note: str = ""

    def low_trust(self) -> bool:
        return self.comparables_n < 10


@dataclass
class ThesisCard:
    """
    Complete package required before a position is proposed.
    Constitution checks: invalidation + profit_take + time_stop.
    base_rate is required here for audit trail.
    """
    symbol: str
    side: str = "buy"
    thesis: str = ""
    invalidation: str = ""
    profit_take: str = ""
    time_stop: str = ""
    base_rate: Optional[BaseRateCard] = None

    def to_guardrail_thesis(self):
        """Return the Thesis object Constitution.evaluate() needs."""
        from guardrail.constitution import Thesis
        return Thesis(
            invalidation=self.invalidation,
            profit_take=self.profit_take,
            time_stop=self.time_stop,
        )

    def is_complete(self) -> bool:
        return bool(
            self.invalidation.strip()
            and self.profit_take.strip()
            and self.time_stop.strip()
        )

    def warnings(self) -> List[str]:
        w: List[str] = []
        if not self.thesis.strip():
            w.append("thesis narrative is empty")
        if self.base_rate is None:
            w.append("no base-rate card attached")
        elif self.base_rate.low_trust():
            w.append(f"low-trust base-rate: N={self.base_rate.comparables_n}")
        return w

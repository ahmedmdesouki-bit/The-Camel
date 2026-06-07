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

    `invalidation` is the PRICE invalidation; S4 adds separate fundamental and Sharia
    invalidation, plus the full standardised template (§5.6) and the opportunity-cost gate.
    """
    symbol: str
    side: str = "buy"
    thesis: str = ""
    invalidation: str = ""              # price invalidation
    profit_take: str = ""
    time_stop: str = ""
    base_rate: Optional[BaseRateCard] = None
    # S4 — full standardised template
    company: str = ""
    regime: str = ""
    theme: str = ""
    sharia_status: str = ""
    time_horizon: str = ""
    signal_summary: str = ""
    why_now: str = ""
    already_priced_in: str = ""
    worst_forward_return: str = ""
    avg_drawdown: str = ""
    valuation_view: str = ""
    liquidity_view: str = ""
    portfolio_fit: str = ""
    fundamental_invalidation: str = ""
    sharia_invalidation: str = ""
    order_type: str = "limit"           # limit by default
    approval_status: str = "pending"
    final_decision: str = ""
    # required skeptic gate: why is this better than just buying more SPUS/HLAL?
    opportunity_cost_justification: str = ""

    def to_guardrail_thesis(self):
        """Return the Thesis object Constitution.evaluate() needs."""
        from guardrail.constitution import Thesis
        return Thesis(
            invalidation=self.invalidation,
            profit_take=self.profit_take,
            time_stop=self.time_stop,
        )

    def is_complete(self) -> bool:
        """Minimum for the Constitution: a complete price invalidation triplet."""
        return bool(
            self.invalidation.strip()
            and self.profit_take.strip()
            and self.time_stop.strip()
        )

    def is_trade_ready(self) -> bool:
        """
        Stricter than is_complete() (S4): also requires the opportunity-cost justification —
        a trade is not ready if it can't answer "why not just buy more SPUS/HLAL?".
        """
        return self.is_complete() and bool(self.opportunity_cost_justification.strip())

    def warnings(self) -> List[str]:
        w: List[str] = []
        if not self.thesis.strip():
            w.append("thesis narrative is empty")
        if not self.opportunity_cost_justification.strip():
            w.append("no opportunity-cost justification (why not just buy more SPUS/HLAL?)")
        if self.base_rate is None:
            w.append("no base-rate card attached")
        elif self.base_rate.low_trust():
            w.append(f"low-trust base-rate: N={self.base_rate.comparables_n}")
        return w

"""
Capital allocator — routes allocation requests through the Constitution.

Rejected requests are logged, never silently clamped — per PRD §5.6 AC:
"allocation requests that would breach a cap are rejected, not clamped silently".
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional

from guardrail.constitution import Action, Constitution, Decision, PortfolioState

log = logging.getLogger(__name__)


@dataclass
class AllocationResult:
    approved: bool
    decision: Decision
    notional_usd: float    # actual approved amount (0.0 if rejected)


class Allocator:
    def __init__(self, constitution: Optional[Constitution] = None):
        self.constitution = constitution or Constitution()

    def request(self, action: Action, state: PortfolioState) -> AllocationResult:
        """
        Evaluate a proposed action.
        Returns AllocationResult — approved=True only if Constitution allows it.
        Never adjusts the notional to fit; rejection is explicit and logged.
        """
        decision = self.constitution.evaluate(action, state)
        if not decision.allow:
            log.warning(
                "Allocator REJECTED %s %s $%.2f — %s [limit_hit=%s]",
                action.side, action.symbol, action.notional_usd,
                decision.reason, decision.limit_hit,
            )
        return AllocationResult(
            approved=decision.allow,
            decision=decision,
            notional_usd=action.notional_usd if decision.allow else 0.0,
        )

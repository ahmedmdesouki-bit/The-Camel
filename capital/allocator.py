"""
Capital allocator — routes allocation requests through the Constitution.

Rejected requests are logged, never silently clamped — per PRD §5.6 AC:
"allocation requests that would breach a cap are rejected, not clamped silently".
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Optional

from guardrail.constitution import Action, ActionType, Constitution, Decision, PortfolioState
from engine.edge_proof_v0 import EdgeReport, gate as edge_gate

log = logging.getLogger(__name__)


def _opens_or_increases(action: Action) -> bool:
    """A market buy/increase needs an Edge Proof; a reduce-only/close (sell) does not."""
    return (getattr(action, "type", None) == ActionType.TRADE
            and str(getattr(action, "side", "")).lower() == "buy")


@dataclass
class AllocationResult:
    approved: bool
    decision: Decision
    notional_usd: float    # actual approved amount (0.0 if rejected)


class Allocator:
    def __init__(self, constitution: Optional[Constitution] = None):
        self.constitution = constitution or Constitution()

    def request(self, action: Action, state: PortfolioState,
                edge_report: Optional[EdgeReport] = None,
                require_edge: Optional[bool] = None) -> AllocationResult:
        """
        Evaluate a proposed action.
        Returns AllocationResult — approved=True only if both the Edge Proof gate (when
        required or when a report is supplied) AND the Constitution allow it.
        Never adjusts the notional to fit; rejection is explicit and logged.

        Edge Proof gate (S4.5 / S6.5): `require_edge` defaults to None, which resolves to
        **True for any market buy/increase** and **False for reduce-only/close (sell) and
        non-trade actions** — opening or adding to a position needs proven edge; de-risking
        does not. Pass require_edge explicitly to override (e.g. False to isolate the
        Constitution path in tests). A required-but-absent EdgeReport, or any supplied report
        that is not `trade_allowed`, blocks the allocator before the Constitution is consulted.
        """
        if require_edge is None:
            require_edge = _opens_or_increases(action)
        if require_edge or edge_report is not None:
            ok, ereason = edge_gate(edge_report)
            if not ok:
                d = Decision(False, f"Edge proof failed: {ereason}", "no_edge_proof")
                log.warning("Allocator REJECTED %s — %s", action.symbol, d.reason)
                return AllocationResult(approved=False, decision=d, notional_usd=0.0)

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

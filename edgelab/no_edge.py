"""
No-Edge protocol (S12) — the honest default when there is no proven edge.

The Camel does NOT need an edge to act well: if no signal proves an edge (Edge Proof fails) but capital
is available, it falls back to **systematic DCA into the compliant core** — which beats most overactive
systems after costs anyway. No edge + no capital → Wait. An active strategy runs ONLY when it both proves
an edge AND beats simple DCA after costs (otherwise DCA is the better, humbler choice).
"""
from __future__ import annotations

from dataclasses import dataclass

DCA_FALLBACK = "core_dca"


@dataclass
class NoEdgeDecision:
    path: str            # "active_strategy" | "core_dca" | "wait"
    reason: str


def resolve_no_edge(edge_allowed: bool, *, has_capital: bool = True,
                    beats_dca: bool = True) -> NoEdgeDecision:
    """Decide the path. An active strategy needs BOTH a proven edge AND to beat DCA after costs."""
    if edge_allowed and beats_dca:
        return NoEdgeDecision("active_strategy", "edge proven and beats DCA after costs")
    if not has_capital:
        return NoEdgeDecision("wait", "no edge and no capital — hold")
    if edge_allowed and not beats_dca:
        return NoEdgeDecision(DCA_FALLBACK, "edge proven but does not beat DCA after costs → DCA")
    return NoEdgeDecision(DCA_FALLBACK, "no proven edge → systematic DCA into the compliant core")


def beats_dca(strategy_return: float, dca_return: float, margin: float = 0.0) -> bool:
    """A strategy earns its place only if it beats simple DCA by at least `margin` (after costs)."""
    return strategy_return > dca_return + margin

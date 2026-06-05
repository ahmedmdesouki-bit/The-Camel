"""
Opportunity Router (S5) — decide whether to Trade, Build, Research, improve the System, or Wait.

"Wait" and "System improvement" are first-class outputs. The router LEANS TOWARD INACTION:
conservative rules fire first (safety gap -> System improvement, missing data/product evidence
-> Research, no capital -> Wait). It can NOT recommend the Trader path without a passing
Edge Proof v0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

# Scoring weights (§11.5) — used to rank eligible paths once the conservative gates pass.
WEIGHTS: Dict[str, float] = {
    "expected_upside": 0.20,
    "evidence_quality": 0.20,
    "downside_risk": 0.20,          # higher input = safer (less downside)
    "sharia_clarity": 0.15,
    "capital_required": 0.10,       # higher input = less capital needed
    "time_required": 0.10,          # higher input = less time needed
    "strategic_learning": 0.05,
}

PATHS = ("trader", "entrepreneur", "research", "system_improvement", "wait")


@dataclass
class RouterInputs:
    # hard gates
    safety_complete: bool = True        # all required safety modules in place
    data_available: bool = True
    capital_available: bool = True
    edge_proven: bool = False           # a passing Edge Proof v0 exists for a trade
    product_evidence: bool = False      # an entrepreneur product case exists
    # soft scoring factors (0..1), used to rank trader vs entrepreneur when both eligible
    factors: Dict[str, float] = field(default_factory=dict)


@dataclass
class RouterDecision:
    recommended_path: str
    reason: str
    confidence: float
    capital_required: float = 0.0
    approval_required: bool = True


def score(factors: Dict[str, float]) -> float:
    """Weighted 0..1 score from the soft factors (missing factor = 0)."""
    return round(sum(WEIGHTS[k] * float(factors.get(k, 0.0)) for k in WEIGHTS), 3)


def route(inputs: RouterInputs, capital_required: float = 0.0) -> RouterDecision:
    # --- conservative gates, in priority order (lean toward inaction) ---
    if not inputs.safety_complete:
        return RouterDecision("system_improvement",
                              "a required safety module is incomplete", 0.9,
                              0.0, approval_required=False)
    if not inputs.data_available:
        return RouterDecision("research", "required data is missing", 0.7,
                              0.0, approval_required=False)
    if not inputs.capital_available:
        return RouterDecision("wait", "no capital budget available", 0.8,
                              0.0, approval_required=False)

    conf = score(inputs.factors)

    # --- trade path requires a passing Edge Proof v0 ---
    if inputs.edge_proven and inputs.product_evidence:
        # both viable → pick the higher-conviction arm; tie favours Entrepreneur (bounded downside)
        path = "trader" if conf >= 0.6 else "entrepreneur"
        return RouterDecision(path, "both arms viable; chose by conviction", conf,
                              capital_required, approval_required=True)
    if inputs.edge_proven:
        return RouterDecision("trader", "edge proven", conf,
                              capital_required, approval_required=True)
    if inputs.product_evidence:
        return RouterDecision("entrepreneur", "product case present, no trade edge", conf,
                              capital_required, approval_required=True)

    # --- nothing proven → do not force action ---
    return RouterDecision("wait", "no proven edge or product case — hold", 0.6,
                          0.0, approval_required=False)

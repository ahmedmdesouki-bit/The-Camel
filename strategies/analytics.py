"""
Quality / income analytics (Alaa-review backlog) — two pure helpers the dividend & quality strategies use.

These are *descriptive* (evidence inputs), not decisions: they never place an order. `yield_on_cost` is the
income investor's true running yield (dividend relative to what you actually paid, not today's price), and
`moat_score` turns a handful of durable-advantage signals into a transparent 0–100 score + a none/narrow/wide
band. Both are deterministic and fully unit-tested; nothing here touches I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


def yield_on_cost(annual_dividend_per_share: float, cost_basis_per_share: float) -> float:
    """Annual dividend ÷ original cost basis (the lot's running yield-on-cost). 0.0 if cost basis ≤ 0."""
    if cost_basis_per_share is None or cost_basis_per_share <= 0:
        return 0.0
    return round(max(0.0, annual_dividend_per_share) / cost_basis_per_share, 6)


# The moat signals we score, each normalised to [0,1] (1 = strongest), with transparent weights.
MOAT_WEIGHTS: Dict[str, float] = {
    "gross_margin_stability": 0.25,   # stable/high gross margin → pricing power
    "roic_above_wacc": 0.25,          # returns on invested capital clearing the cost of capital
    "market_share_trend": 0.20,       # holding/gaining share
    "switching_costs": 0.15,          # customer lock-in
    "net_cash_strength": 0.15,        # balance-sheet durability (also helps the AAOIFI debt screen)
}


@dataclass
class MoatAssessment:
    score: float            # 0–100
    band: str               # "none" | "narrow" | "wide"
    contributions: Dict[str, float]


def moat_score(signals: Dict[str, float]) -> MoatAssessment:
    """Weighted 0–100 moat score from normalised [0,1] signals. Unknown signals default to 0 (conservative);
    a name only earns 'wide' on broad, durable strength — not one strong line."""
    contributions: Dict[str, float] = {}
    total = 0.0
    for key, weight in MOAT_WEIGHTS.items():
        v = signals.get(key, 0.0)
        v = 0.0 if v is None else max(0.0, min(1.0, float(v)))
        contrib = round(v * weight * 100, 4)
        contributions[key] = contrib
        total += contrib
    score = round(total, 2)
    band = "wide" if score >= 70 else "narrow" if score >= 40 else "none"
    return MoatAssessment(score=score, band=band, contributions=contributions)

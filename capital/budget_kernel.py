"""
Budget Kernel (S4) — controls capital allocation before any action touches money.

Deterministic and founder-owned: daily / weekly / monthly / per-action spend limits, plus
capital buckets (Core / Trader / Entrepreneur / System / Emergency). Every spend request is
checked here BEFORE the Constitution sizing checks. Rejections are explicit, never clamped.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class BudgetLimits:
    total_fund: float
    max_per_action: float
    max_daily_spend: float
    max_weekly_spend: float
    max_monthly_spend: float
    # bucket name -> fraction of total_fund (founder-owned; should sum to ~1.0)
    buckets: Dict[str, float] = field(default_factory=lambda: {
        "core": 0.50, "trader": 0.15, "entrepreneur": 0.20,
        "system": 0.05, "emergency": 0.10,
    })


@dataclass
class BudgetState:
    spent_today: float = 0.0
    spent_week: float = 0.0
    spent_month: float = 0.0


@dataclass
class BudgetDecision:
    allow: bool
    reason: str
    limit_hit: str = ""


class BudgetKernel:
    def __init__(self, limits: BudgetLimits):
        self.L = limits

    def bucket_allocation(self, bucket: str) -> float:
        """Dollar allocation for a named bucket (total_fund * its fraction)."""
        return self.L.total_fund * self.L.buckets.get(bucket, 0.0)

    def buckets_sum(self) -> float:
        return sum(self.L.buckets.values())

    def check(self, amount: float, state: BudgetState) -> BudgetDecision:
        """Check a proposed spend `amount` against per-action + rolling limits."""
        if amount < 0:
            return BudgetDecision(False, "Negative spend is not a budget action.", "negative")
        if amount > self.L.max_per_action + 1e-9:
            return BudgetDecision(False, "Exceeds per-action spend limit.", "per_action")
        if state.spent_today + amount > self.L.max_daily_spend + 1e-9:
            return BudgetDecision(False, "Exceeds daily spend limit.", "daily")
        if state.spent_week + amount > self.L.max_weekly_spend + 1e-9:
            return BudgetDecision(False, "Exceeds weekly spend limit.", "weekly")
        if state.spent_month + amount > self.L.max_monthly_spend + 1e-9:
            return BudgetDecision(False, "Exceeds monthly spend limit.", "monthly")
        return BudgetDecision(True, "Within budget.")

"""
Realistic-paper executor (S12) — the decision-validation execution rail.

Wraps the fill model with config (fees, max quote age) and the whole-share constraint (Sahm). It is
NOT broker paper: it crosses the real spread, partial-fills against displayed size, charges fees, and
**rejects stale data** instead of inventing a price. No performance number may ever come from
`loop_test` (last-close / $1 fallback) — only from this engine or the sandbox that drives it.
"""
from __future__ import annotations

from typing import Optional

from execution.models import Order, MarketSnapshot, Fill, FillStatus
from execution.fill import simulate_fill, DEFAULT_FEE_BPS, DEFAULT_MAX_AGE_S


class RealisticPaperExecutor:
    def __init__(self, *, fee_bps: float = DEFAULT_FEE_BPS, max_age_s: float = DEFAULT_MAX_AGE_S,
                 whole_shares: bool = True):
        self.fee_bps = fee_bps
        self.max_age_s = max_age_s
        self.whole_shares = whole_shares      # Sahm: no fractional shares

    def execute(self, order: Order, snapshot: MarketSnapshot, *, now: Optional[str] = None) -> Fill:
        if self.whole_shares and order.qty != int(order.qty):
            return Fill(order.symbol, order.side, order.qty, 0.0, 0.0, 0.0, 0.0, FillStatus.REJECTED,
                        "whole-share constraint (Sahm) — fractional order refused")
        return simulate_fill(order, snapshot, fee_bps=self.fee_bps, max_age_s=self.max_age_s, now=now)

"""core_dca (S11) — systematic monthly DCA into an approved core ETF. No market timing."""
from __future__ import annotations

from typing import List

from trader.strategies.base import BaseStrategy, Signal, StrategyContext, StrategyMeta, PromotionMode


class CoreDCA(BaseStrategy):
    """Buy the core ETF on a fixed schedule regardless of price — likely beats most overactive systems
    after costs. Zero timing; the only judgement is *which* compliant core ETF."""

    def __init__(self, core_etf: str = "SPUS"):
        self.core_etf = core_etf
        self.meta = StrategyMeta(
            id="core_dca", name="Core DCA", thesis_family="systematic_accumulation",
            mode=PromotionMode.REALISTIC_PAPER, applicable_regimes=[],   # all regimes
            max_single_position=0.60, min_signal_confidence=0.0, base_rate=0.55,
        )

    def generate_signals(self, ctx: StrategyContext) -> List[Signal]:
        return [Signal(symbol=self.core_etf, action="buy", confidence=0.7,
                       strategy_id=self.meta.id, theme="core",
                       rationale="scheduled DCA into the compliant core ETF (no timing)")]

"""
quality_momentum (S11) — factor-driven, low-turnover. 12-1 momentum on compliant names.

12-1 momentum = price 1 month ago ÷ price 12 months ago − 1 (skip the most recent month to avoid the
short-term reversal). A positive, strong trend on a Sharia-clear name → a buy proposal whose confidence
scales with the trend. Still passes the full Edge Proof + Constitution downstream.
"""
from __future__ import annotations

from typing import List

from trader.strategies.base import BaseStrategy, Signal, StrategyContext, StrategyMeta, PromotionMode

_LOOKBACK = 252          # ~12 months of trading days
_SKIP = 21               # ~1 month
_MIN_MOMENTUM = 0.05     # require ≥ +5% 12-1 momentum to propose


def momentum_12_1(closes: List[float]) -> float:
    """Pure: 12-1 momentum. 0.0 if not enough history."""
    if len(closes) < _LOOKBACK + 1:
        return 0.0
    old = closes[-_LOOKBACK]
    recent = closes[-_SKIP]
    return (recent / old - 1.0) if old else 0.0


class QualityMomentum(BaseStrategy):
    def __init__(self):
        self.meta = StrategyMeta(
            id="quality_momentum", name="Quality Momentum", thesis_family="factor_momentum",
            mode=PromotionMode.BACKTEST,
            applicable_regimes=["LIQUIDITY_EXPANSION", "DISINFLATION_GROWTH", "RECOVERY",
                                "AI_CAPEX_BOOM", "UNKNOWN"],
            max_single_position=0.15, min_signal_confidence=0.3, base_rate=0.52,
        )

    def generate_signals(self, ctx: StrategyContext) -> List[Signal]:
        out: List[Signal] = []
        for symbol, closes in ctx.closes.items():
            mom = momentum_12_1(closes)
            if mom >= _MIN_MOMENTUM:
                out.append(Signal(symbol=symbol, action="buy",
                                  confidence=round(min(1.0, mom * 2.0), 3),
                                  strategy_id=self.meta.id, theme="momentum",
                                  rationale=f"12-1 momentum {mom:.1%} ≥ {_MIN_MOMENTUM:.0%}"))
        return out

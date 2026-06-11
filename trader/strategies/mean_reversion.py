"""
mean_reversion (S11 backlog, built S17) — buy short-term dips, never catch a falling knife.

Buys a Sharia-clear name when it has dipped a meaningful amount BELOW its short moving average (oversold)
— BUT only while it is still ABOVE its long-term trend MA. The long-trend filter is the whole safety of
the strategy: a dip inside an uptrend mean-reverts; a dip below a broken trend is a falling knife and is
NOT bought. Proposes only; the full Edge Proof + Constitution still decide downstream.
"""
from __future__ import annotations

from typing import List

from trader.strategies.base import BaseStrategy, Signal, StrategyContext, StrategyMeta, PromotionMode

_SHORT_MA = 20           # short window for the dip measure
_TREND_MA = 200          # long-term trend filter (no falling knives)
_MIN_DIP = 0.03          # require >= 3% below the short MA to call it oversold


def pct_below_ma(closes: List[float], window: int = _SHORT_MA) -> float:
    """Pure: how far the latest close sits BELOW its `window`-bar MA, as a positive fraction (a dip).
    <= 0 means at/above the MA. 0.0 if not enough history."""
    if len(closes) < window:
        return 0.0
    ma = sum(closes[-window:]) / window
    return (ma - closes[-1]) / ma if ma else 0.0


def above_trend(closes: List[float], window: int = _TREND_MA) -> bool:
    if len(closes) < window:
        return False
    ma = sum(closes[-window:]) / window
    return ma > 0 and closes[-1] > ma


class MeanReversion(BaseStrategy):
    def __init__(self):
        self.meta = StrategyMeta(
            id="mean_reversion", name="Mean Reversion", thesis_family="mean_reversion",
            mode=PromotionMode.BACKTEST,
            applicable_regimes=["LIQUIDITY_EXPANSION", "DISINFLATION_GROWTH", "RECOVERY", "UNKNOWN"],
            max_single_position=0.10, min_signal_confidence=0.3, base_rate=0.50,
        )

    def generate_signals(self, ctx: StrategyContext) -> List[Signal]:
        out: List[Signal] = []
        for symbol, closes in ctx.closes.items():
            dip = pct_below_ma(closes)
            if dip >= _MIN_DIP and above_trend(closes):       # oversold dip INSIDE an intact uptrend
                out.append(Signal(symbol=symbol, action="buy",
                                  confidence=round(min(1.0, 0.3 + dip * 4), 3),
                                  strategy_id=self.meta.id, theme="mean_reversion",
                                  rationale=f"{dip:.1%} below the {_SHORT_MA}d MA, still above the "
                                            f"{_TREND_MA}d trend"))
        return out

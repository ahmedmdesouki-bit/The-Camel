"""
ts_momentum (S11 backlog, built S17) — time-series (absolute) momentum.

Distinct from `quality_momentum` (which is CROSS-SECTIONAL 12-1, comparing names against each other):
this is ABSOLUTE / time-series momentum (TSMOM) — go long a name only when its OWN trailing 12-month
return is positive (it is beating cash/holding-flat), with a trend filter (price above its long MA).
A defensive, well-evidenced factor: positive own-trend + above the long average → a buy whose confidence
scales with trend strength. Still passes the full Edge Proof + Constitution downstream; proposes only.
"""
from __future__ import annotations

from typing import List

from trader.strategies.base import BaseStrategy, Signal, StrategyContext, StrategyMeta, PromotionMode

_LOOKBACK = 252          # ~12 months of trading days
_TREND_MA = 200          # long-term trend filter
_MIN_RETURN = 0.0        # require a POSITIVE own trailing return (beating flat/cash)


def trailing_return(closes: List[float], lookback: int = _LOOKBACK) -> float:
    """Pure: own trailing total return over `lookback` bars. 0.0 if not enough history."""
    if len(closes) < lookback + 1:
        return 0.0
    old = closes[-lookback - 1]
    return (closes[-1] / old - 1.0) if old else 0.0


def above_trend(closes: List[float], window: int = _TREND_MA) -> bool:
    """Pure: is the latest close above its `window`-bar moving average? (no history → False, fail-safe)."""
    if len(closes) < window:
        return False
    ma = sum(closes[-window:]) / window
    return ma > 0 and closes[-1] > ma


class TimeSeriesMomentum(BaseStrategy):
    def __init__(self):
        self.meta = StrategyMeta(
            id="ts_momentum", name="Time-Series Momentum", thesis_family="absolute_momentum",
            mode=PromotionMode.BACKTEST,
            applicable_regimes=["LIQUIDITY_EXPANSION", "DISINFLATION_GROWTH", "RECOVERY",
                                "AI_CAPEX_BOOM", "UNKNOWN"],
            max_single_position=0.15, min_signal_confidence=0.3, base_rate=0.52,
        )

    def generate_signals(self, ctx: StrategyContext) -> List[Signal]:
        out: List[Signal] = []
        for symbol, closes in ctx.closes.items():
            r = trailing_return(closes)
            if r > _MIN_RETURN and above_trend(closes):       # positive own-trend AND above the long MA
                out.append(Signal(symbol=symbol, action="buy",
                                  confidence=round(min(1.0, 0.3 + r), 3),
                                  strategy_id=self.meta.id, theme="momentum",
                                  rationale=f"12-mo own return {r:.1%} > 0 and above the {_TREND_MA}d trend"))
        return out

"""
etf_regime_rotation (S11) — rotate among compliant ETFs (SPUS / HLAL / MNZL) or cash by regime.

Only proposes if it beats simple DCA after costs (proven in the Edge Lab, S12). A risk-off regime maps
to CASH (no buy) — the strategy's job is sometimes to step aside.
"""
from __future__ import annotations

from typing import List, Optional

from strategies.base import BaseStrategy, Signal, StrategyContext, StrategyMeta, PromotionMode

# regime → target compliant ETF (None = hold cash / step aside)
_REGIME_TARGET = {
    "LIQUIDITY_EXPANSION": "SPUS",
    "DISINFLATION_GROWTH": "SPUS",
    "RECOVERY": "SPUS",
    "AI_CAPEX_BOOM": "SPUS",
    "LIQUIDITY_TIGHTENING": "HLAL",       # quality tilt
    "USD_STRENGTH_EM_PRESSURE": "HLAL",
    "INFLATION_SHOCK": "MNZL",            # real-asset / value tilt
    "COMMODITY_SUPPLY_SHOCK": "MNZL",
    "GEOPOLITICAL_RISK_OFF": None,        # cash
    "RECESSION_RISK": None,               # cash
}


def target_etf(regime: str) -> Optional[str]:
    return _REGIME_TARGET.get(regime, "SPUS")     # default to the core ETF


class ETFRegimeRotation(BaseStrategy):
    def __init__(self):
        self.meta = StrategyMeta(
            id="etf_regime_rotation", name="ETF Regime Rotation", thesis_family="regime_rotation",
            mode=PromotionMode.BACKTEST, applicable_regimes=[],   # all (it decides cash vs ETF itself)
            max_single_position=0.50, min_signal_confidence=0.3, base_rate=0.50,
        )

    def generate_signals(self, ctx: StrategyContext) -> List[Signal]:
        target = target_etf(ctx.regime)
        if target is None:
            return [Signal(symbol="CASH", action="hold", confidence=0.6, strategy_id=self.meta.id,
                           theme="defensive", rationale=f"{ctx.regime} → hold cash, step aside")]
        return [Signal(symbol=target, action="buy", confidence=0.55, strategy_id=self.meta.id,
                       theme="rotation", rationale=f"{ctx.regime} → rotate into {target}")]

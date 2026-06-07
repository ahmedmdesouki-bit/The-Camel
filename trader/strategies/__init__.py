"""Strategy framework + starter trio + dividend growth + mixer (S11)."""
from trader.strategies.base import (
    BaseStrategy, Signal, StrategyContext, StrategyMeta, StrategyStatus, PromotionMode,
    MODE_LADDER, can_promote, demote,
)
from trader.strategies.registry import StrategyRegistry
from trader.strategies.mixer import StrategyMixer, BlendedCandidate
from trader.strategies.core_dca import CoreDCA
from trader.strategies.quality_momentum import QualityMomentum, momentum_12_1
from trader.strategies.etf_rotation import ETFRegimeRotation, target_etf
from trader.strategies.dividend_growth import DividendGrowth, DividendProfile
from trader.strategies.dividends import net_dividend, purification_amount, DividendCash

__all__ = [
    "BaseStrategy", "Signal", "StrategyContext", "StrategyMeta", "StrategyStatus", "PromotionMode",
    "MODE_LADDER", "can_promote", "demote", "StrategyRegistry", "StrategyMixer", "BlendedCandidate",
    "CoreDCA", "QualityMomentum", "momentum_12_1", "ETFRegimeRotation", "target_etf",
    "DividendGrowth", "DividendProfile", "net_dividend", "purification_amount", "DividendCash",
]

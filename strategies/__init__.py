"""Strategy framework + starter trio + dividend growth + mixer (S11)."""
from strategies.base import (
    BaseStrategy, Signal, StrategyContext, StrategyMeta, StrategyStatus, PromotionMode,
    MODE_LADDER, can_promote, demote,
)
from strategies.registry import StrategyRegistry
from strategies.mixer import StrategyMixer, BlendedCandidate
from strategies.core_dca import CoreDCA
from strategies.quality_momentum import QualityMomentum, momentum_12_1
from strategies.etf_rotation import ETFRegimeRotation, target_etf
from strategies.dividend_growth import DividendGrowth, DividendProfile
from strategies.dividends import net_dividend, purification_amount, DividendCash

__all__ = [
    "BaseStrategy", "Signal", "StrategyContext", "StrategyMeta", "StrategyStatus", "PromotionMode",
    "MODE_LADDER", "can_promote", "demote", "StrategyRegistry", "StrategyMixer", "BlendedCandidate",
    "CoreDCA", "QualityMomentum", "momentum_12_1", "ETFRegimeRotation", "target_etf",
    "DividendGrowth", "DividendProfile", "net_dividend", "purification_amount", "DividendCash",
]

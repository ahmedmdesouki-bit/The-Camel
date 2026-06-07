"""
dividend_growth (S11) — Sharia-screened QUALITY INCOME (not dividend capture).

Buys compliant businesses with a durable, growing payout and a sane payout ratio; the impure portion is
purified (S9 purification_ratio + `strategies/dividends.py`). This is dividend-*growth*, deliberately NOT
dividend-*capture* (buy-before / sell-after-ex-div rarely survives costs + whole-share constraints, and the
Edge Proof would reject it). The dividend fundamentals plug in via EODHD (S8 backlog); the strategy logic
here proposes from a curated candidate set filtered to Sharia-clear, low-payout, growth-streak names.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from trader.strategies.base import BaseStrategy, Signal, StrategyContext, StrategyMeta, PromotionMode

_MAX_PAYOUT = 0.70           # avoid unsustainable payouts
_MIN_STREAK = 5              # ≥ 5 years of consecutive dividend growth


@dataclass
class DividendProfile:
    symbol: str
    payout_ratio: float
    growth_streak_years: int
    yield_pct: float = 0.0


class DividendGrowth(BaseStrategy):
    def __init__(self, candidates: Dict[str, DividendProfile] = None):
        # curated candidates (fundamentals land via EODHD, S8 backlog); empty = nothing proposed yet
        self.candidates = candidates or {}
        self.meta = StrategyMeta(
            id="dividend_growth", name="Dividend Growth (quality income)", thesis_family="quality_income",
            mode=PromotionMode.BACKTEST, applicable_regimes=[],   # income is regime-agnostic
            max_single_position=0.10, min_signal_confidence=0.3, base_rate=0.53,
        )

    def generate_signals(self, ctx: StrategyContext) -> List[Signal]:
        out: List[Signal] = []
        for symbol, p in self.candidates.items():
            if p.payout_ratio <= _MAX_PAYOUT and p.growth_streak_years >= _MIN_STREAK:
                conf = round(min(1.0, 0.4 + 0.1 * (p.growth_streak_years - _MIN_STREAK)), 3)
                out.append(Signal(symbol=symbol, action="buy", confidence=conf,
                                  strategy_id=self.meta.id, theme="income",
                                  rationale=f"{p.growth_streak_years}y dividend growth, payout {p.payout_ratio:.0%}"))
        return out

"""
dca_ladder (S11 backlog, built S17) — tranche DCA into dips, WITH the rules that make averaging-down safe.

The Constitution DO-NOT rail is explicit: "do not average down into individual stocks blindly." This
strategy is the *safe* form of averaging down, and it enforces the rules in code, not in hope:

  1. ETF-ONLY. It proposes ONLY for names in an explicit ETF universe (default SPUS/HLAL/MNZL). It will
     never ladder into a single stock — averaging down a single name is how you marry a loser.
  2. Tranche on a real dip. It adds only when price is >= one rung below the recent high.
  3. DETERIORATION GUARD. It STOPS laddering the moment price falls below its long-term trend MA — a dip
     inside an uptrend is an opportunity; a dip below a broken trend is a falling knife. No tranche there.

Proposes only; the full Edge Proof + Constitution + Budget still decide downstream.
"""
from __future__ import annotations

from typing import List, Optional, Set

from trader.strategies.base import BaseStrategy, Signal, StrategyContext, StrategyMeta, PromotionMode

_RUNG = 0.05             # add a tranche each 5% of drawdown from the recent high
_HIGH_WINDOW = 63        # ~3 months: the "recent high" the drawdown is measured from
_TREND_MA = 200          # deterioration guard: below this long MA → trend broken → stop laddering
_DEFAULT_ETFS = frozenset({"SPUS", "HLAL", "MNZL"})


def drawdown_from_high(closes: List[float], window: int = _HIGH_WINDOW) -> float:
    """Pure: drawdown of the latest close from the rolling `window` high, as a positive fraction."""
    if not closes:
        return 0.0
    recent = closes[-window:] if len(closes) >= window else closes
    hi = max(recent)
    return (hi - closes[-1]) / hi if hi else 0.0


def above_trend(closes: List[float], window: int = _TREND_MA) -> bool:
    if len(closes) < window:
        return False
    ma = sum(closes[-window:]) / window
    return ma > 0 and closes[-1] > ma


def ladder_rungs(closes: List[float], rung: float = _RUNG) -> int:
    """How many `rung`-sized tranches the current drawdown justifies (0 if not down a full rung)."""
    dd = drawdown_from_high(closes)
    return int(dd // rung) if rung > 0 else 0


class DCALadder(BaseStrategy):
    def __init__(self, etf_universe: Optional[Set[str]] = None):
        self.etfs = set(etf_universe) if etf_universe else set(_DEFAULT_ETFS)
        self.meta = StrategyMeta(
            id="dca_ladder", name="DCA Ladder", thesis_family="systematic_accumulation",
            mode=PromotionMode.BACKTEST, applicable_regimes=[],   # all regimes (it has its own guard)
            max_single_position=0.40, min_signal_confidence=0.0, base_rate=0.53,
        )

    def generate_signals(self, ctx: StrategyContext) -> List[Signal]:
        out: List[Signal] = []
        for symbol, closes in ctx.closes.items():
            if symbol not in self.etfs:                       # RULE 1: ETF-only — never a single stock
                continue
            if not above_trend(closes):                       # RULE 3: trend broken → no tranche (knife)
                continue
            rungs = ladder_rungs(closes)                      # RULE 2: only add on a real dip
            if rungs >= 1:
                dd = drawdown_from_high(closes)
                out.append(Signal(symbol=symbol, action="buy",
                                  confidence=round(min(1.0, 0.4 + 0.1 * rungs), 3),
                                  strategy_id=self.meta.id, theme="ladder",
                                  rationale=f"{dd:.1%} off the {_HIGH_WINDOW}d high ({rungs} rung(s)), "
                                            f"still above the {_TREND_MA}d trend"))
        return out

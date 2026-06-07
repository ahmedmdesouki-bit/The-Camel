"""
StrategyMixer (S11) — blend signals from multiple strategies into ranked candidates.

When several strategies propose the same name, their convictions combine — weighted by each strategy's
registry weight (L2 learning sets these within a founder band; unset = equal). Output is a ranked list of
buy candidates that the portfolio engine sizes and the assembled loop runs through Edge Proof. The mixer
PROPOSES a ranking; it sizes nothing and gates nothing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from trader.strategies.base import Signal
from trader.strategies.registry import StrategyRegistry


@dataclass
class BlendedCandidate:
    symbol: str
    confidence: float
    theme: str = ""
    strategies: List[str] = field(default_factory=list)


def _weight(registry: StrategyRegistry, sid: str) -> float:
    s = registry.get(sid)
    w = s.meta.weight if s else 0.0
    return w if w > 0 else 1.0          # unset weight → blend equally


class StrategyMixer:
    def blend(self, signals: List[Signal], registry: StrategyRegistry) -> List[BlendedCandidate]:
        agg = {}   # symbol -> [weighted_conf_sum, weight_sum, themes, sids]
        for s in signals:
            if s.action != "buy":
                continue
            w = _weight(registry, s.strategy_id)
            acc = agg.setdefault(s.symbol, [0.0, 0.0, set(), []])
            acc[0] += w * s.confidence
            acc[1] += w
            if s.theme:
                acc[2].add(s.theme)
            acc[3].append(s.strategy_id)
        out = [BlendedCandidate(symbol=sym,
                                confidence=round(c_sum / w_sum, 3) if w_sum else 0.0,
                                theme="/".join(sorted(themes)), strategies=sids)
               for sym, (c_sum, w_sum, themes, sids) in agg.items()]
        return sorted(out, key=lambda c: c.confidence, reverse=True)

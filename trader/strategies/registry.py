"""
Strategy Registry (S11) — versioned registry, the promotion ladder, and the strategy-portfolio matrix.

Not a folder of scripts: every strategy is registered with metadata, a promotion `mode`, allowed/forbidden
portfolios + caps, and kill criteria. The registry is what promotion, rollback, weighting, and audit run on.
It NEVER auto-edits the Constitution, and weight changes are bounded (L2 learning moves weight only within a
founder-set band; L3/L4 changes are propose-only / founder-only).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from trader.strategies.base import (
    BaseStrategy, Signal, StrategyContext, StrategyStatus, PromotionMode,
    can_promote, demote as _demote,
)


class StrategyRegistry:
    def __init__(self):
        self._strats: Dict[str, BaseStrategy] = {}

    # ---- registration / lookup ----
    def register(self, strategy: BaseStrategy) -> None:
        sid = strategy.meta.id
        if sid in self._strats:
            raise ValueError(f"strategy '{sid}' already registered")
        self._strats[sid] = strategy

    def get(self, sid: str) -> Optional[BaseStrategy]:
        return self._strats.get(sid)

    def all(self) -> List[BaseStrategy]:
        return list(self._strats.values())

    def active(self) -> List[BaseStrategy]:
        return [s for s in self._strats.values() if s.meta.status == StrategyStatus.ACTIVE]

    # ---- lifecycle ----
    def set_status(self, sid: str, status: StrategyStatus) -> None:
        self._strats[sid].meta.status = status

    def pause(self, sid: str) -> None:   self.set_status(sid, StrategyStatus.PAUSED)
    def activate(self, sid: str) -> None: self.set_status(sid, StrategyStatus.ACTIVE)
    def kill(self, sid: str) -> None:     self.set_status(sid, StrategyStatus.KILLED)
    def retire(self, sid: str) -> None:   self.set_status(sid, StrategyStatus.RETIRED)

    # ---- weighting (L2: only within a founder-set band) ----
    def set_weight(self, sid: str, weight: float, band: tuple = (0.0, 1.0)) -> float:
        lo, hi = band
        clamped = max(lo, min(hi, weight))
        self._strats[sid].meta.weight = clamped
        return clamped

    # ---- promotion ladder (one rung at a time; failure demotes to cooldown) ----
    def promote(self, sid: str) -> PromotionMode:
        meta = self._strats[sid].meta
        nxt = can_promote(meta.mode)
        if nxt is not None:
            meta.mode = nxt
        return meta.mode

    def demote(self, sid: str) -> PromotionMode:
        meta = self._strats[sid].meta
        meta.mode = _demote(meta.mode)
        return meta.mode

    # ---- the strategy-portfolio matrix + regime filter ----
    def signals_for(self, ctx: StrategyContext, portfolio_id: Optional[str] = None) -> List[Signal]:
        """Collect signals from every ACTIVE strategy that (a) runs in the current regime and (b) is
        allowed in the given portfolio. Each strategy applies its own confidence/tradeable filter."""
        out: List[Signal] = []
        for s in self.active():
            if not s.meta.runs_in_regime(ctx.regime):
                continue
            if portfolio_id is not None and not s.meta.allowed_in(portfolio_id):
                continue
            out.extend(s._filter(s.generate_signals(ctx), ctx))
        return out

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


class PromotionEvidenceError(RuntimeError):
    """Raised when a promotion is requested without the track record to back it (S16-A5)."""


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
    # S16-A5: a rung is EARNED, never granted. Promotion requires either a real track record
    # (evidence = {"base_rate": ..., "n": ...} from `strategy_base_rates`, via
    # learning.measure.strategy_evidence) or the founder's explicit, named override.
    MIN_EVIDENCE_N = 20            # resolved round-trips before any rung advances
    MIN_EVIDENCE_BASE_RATE = 0.5   # the track record must at least not refute the strategy

    def promote(self, sid: str, *, evidence: Optional[dict] = None,
                by_founder: str = "") -> PromotionMode:
        """Advance one rung IFF the evidence clears the bar (or a named founder overrides).

        ALLOW-ON-PROOF (not refuse-on-bad): the rung advances only when the evidence affirmatively
        clears every check — so a NaN/garbage base_rate FAILS (a NaN survives any refuse-comparison;
        QA-probed). The two LIVE rungs are FOUNDER-ONLY regardless of evidence: no track record, however
        good, lets the agent promote itself into real money — that is the founder's explicit act.

        Raises PromotionEvidenceError otherwise."""
        import math
        meta = self._strats[sid].meta
        nxt = can_promote(meta.mode)
        if nxt is None:
            return meta.mode
        founder = bool((by_founder or "").strip())
        if nxt in (PromotionMode.LIVE_SMALL, PromotionMode.LIVE_SCALE) and not founder:
            raise PromotionEvidenceError(
                f"promotion of '{sid}' to {nxt.value} refused: live rungs are founder-only — "
                f"evidence earns paper autonomy, never live capital.")
        if not founder:
            ev = evidence or {}
            try:
                n = int(ev.get("n", 0) or 0)
                br = float(ev.get("base_rate", 0.0) or 0.0)
            except (TypeError, ValueError):
                n, br = 0, 0.0
            ok = (n >= self.MIN_EVIDENCE_N
                  and math.isfinite(br)
                  and br >= self.MIN_EVIDENCE_BASE_RATE)
            if not ok:
                raise PromotionEvidenceError(
                    f"promotion of '{sid}' to {nxt.value} refused: evidence n={n} (need "
                    f">={self.MIN_EVIDENCE_N}), base_rate={br!r} (need finite and >="
                    f"{self.MIN_EVIDENCE_BASE_RATE:.2f}). Autonomy is earned, not granted.")
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

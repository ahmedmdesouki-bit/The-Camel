"""
Strategy framework (S11) — the contract every strategy obeys.

A strategy PROPOSES; it never executes. `generate_signals(context)` returns structured `Signal`s that
flow into the assembled loop (S10.5) → Edge Proof (S10) → Allocator (Constitution) → Budget → Approval.
The strategy cannot size in dollars, touch the ledger, or bypass a gate — trust inversion intact.

Each strategy carries registry metadata: its promotion `mode` (the S11 ladder), allowed/forbidden
portfolios + caps (the strategy-portfolio matrix), applicable regimes, and kill criteria. Strategies
are pure (no I/O) so they are deterministic and unit-testable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class StrategyStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    KILLED = "killed"
    RETIRED = "retired"


class PromotionMode(str, Enum):
    """The per-strategy promotion ladder (consultant-adopted). One rung at a time; failure demotes."""
    BACKTEST = "backtest"
    REALISTIC_PAPER = "realistic_paper"
    SHADOW = "shadow"
    LIVE_SMALL = "live_small"
    LIVE_SCALE = "live_scale"


MODE_LADDER = [PromotionMode.BACKTEST, PromotionMode.REALISTIC_PAPER, PromotionMode.SHADOW,
               PromotionMode.LIVE_SMALL, PromotionMode.LIVE_SCALE]


@dataclass
class Signal:
    symbol: str
    action: str                       # "buy" | "hold" | "avoid" | "reduce"
    confidence: float                 # 0..1
    strategy_id: str
    rationale: str = ""
    theme: str = ""


@dataclass
class StrategyContext:
    """Everything a strategy may read — point-in-time, read-only. No DB handles."""
    as_of: Optional[str] = None
    regime: str = "UNKNOWN"
    themes: List[str] = field(default_factory=list)
    closes: Dict[str, List[float]] = field(default_factory=dict)   # symbol -> ascending closes
    whitelist: Dict[str, str] = field(default_factory=dict)        # symbol -> sharia status
    holdings: Dict[str, float] = field(default_factory=dict)       # symbol -> qty held
    cash_usd: float = 0.0


@dataclass
class StrategyMeta:
    id: str
    name: str
    version: str = "0.1.0"
    thesis_family: str = ""
    mode: PromotionMode = PromotionMode.BACKTEST
    status: StrategyStatus = StrategyStatus.ACTIVE
    applicable_regimes: List[str] = field(default_factory=list)    # empty = all regimes
    allowed_portfolios: List[str] = field(default_factory=list)    # empty = any non-forbidden
    forbidden_portfolios: List[str] = field(default_factory=list)
    max_portfolio_weight: float = 1.0
    max_single_position: float = 0.20
    min_signal_confidence: float = 0.0
    requires_edge_proof: bool = True
    weight: float = 0.0               # current blend weight (L2 learning adjusts within a band)
    base_rate: float = 0.5            # prior hit-rate (L1 learning updates)
    kill_criteria: Dict = field(default_factory=dict)

    def runs_in_regime(self, regime: str) -> bool:
        return not self.applicable_regimes or regime in self.applicable_regimes

    def allowed_in(self, portfolio_id: str) -> bool:
        if portfolio_id in self.forbidden_portfolios:
            return False
        return not self.allowed_portfolios or portfolio_id in self.allowed_portfolios


class BaseStrategy:
    """Abstract strategy. Subclasses set `meta` and implement `generate_signals`."""

    meta: StrategyMeta

    def generate_signals(self, ctx: StrategyContext) -> List[Signal]:   # pragma: no cover - abstract
        raise NotImplementedError

    # ---- shared safety helpers (every strategy must honour these) ----
    def _is_tradeable(self, symbol: str, ctx: StrategyContext) -> bool:
        """Only propose names that are whitelisted AND a clear Sharia pass. Fail-safe: unknown → no."""
        status = (ctx.whitelist.get(symbol) or "").lower()
        return status in ("pass", "compliant")

    def _filter(self, signals: List[Signal], ctx: StrategyContext) -> List[Signal]:
        """Drop signals below the confidence floor or for non-tradeable names (defence in depth —
        the Sharia gate also enforces this downstream, but a strategy must never *propose* a haram name)."""
        return [s for s in signals
                if s.confidence >= self.meta.min_signal_confidence
                and (s.action in ("hold", "avoid", "reduce") or self._is_tradeable(s.symbol, ctx))]


def can_promote(mode: PromotionMode) -> Optional[PromotionMode]:
    """Next rung up the ladder, or None at the top."""
    i = MODE_LADDER.index(mode)
    return MODE_LADDER[i + 1] if i + 1 < len(MODE_LADDER) else None


def demote(mode: PromotionMode) -> PromotionMode:
    """Failure → drop to realistic_paper cooldown (never deletes)."""
    return PromotionMode.REALISTIC_PAPER if mode != PromotionMode.BACKTEST else PromotionMode.BACKTEST

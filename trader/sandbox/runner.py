"""
Sandbox Mode (S12) ⭐ — the full system on LIVE data with VIRTUAL money.

This is the live dress rehearsal: it drives the *entire* assembled loop — Observe(regime) → strategies
(S11) → the full Edge Proof (S10) → Constitution + Budget + Approval (S10.5) — exactly as production
would, but every fill goes through the **realistic-paper executor** (S12a) against a **live quote feed**
instead of a real broker. No real money, full system power. The track record it produces (every accept,
reject, and fill) is what gates micro-live (S13).

The quote `feed` is injected (Callable[[symbol], MarketSnapshot]) — in production it's the Alpaca IEX /
Finnhub websocket; in tests it's a stub. So the sandbox is fully testable with no network. The decision
logic is never bypassed: a candidate still has to pass Edge Proof + the Constitution before a virtual
order is even built, and the realistic executor can still reject a stale quote or non-marketable limit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from db.paths import CamelDbs
from guardrail.constitution import Action, PortfolioState
from trader.strategies.registry import StrategyRegistry
from loop.assembled import AssembledLoop, TickResult
from loop.driver import run_strategy_tick
from trader.execution.models import Order, MarketSnapshot, Fill, FillStatus
from trader.execution.realistic_paper import RealisticPaperExecutor
from trader.edgelab.no_edge import resolve_no_edge


@dataclass
class SandboxTick:
    tick: Optional[TickResult] = None
    fills: List[Fill] = field(default_factory=list)
    no_edge: str = ""              # the No-Edge protocol decision when nothing traded

    @property
    def filled(self) -> List[str]:
        return [f.symbol for f in self.fills if f.status in (FillStatus.FILLED, FillStatus.PARTIAL)]


class SandboxRunner:
    """Virtual-money execution of the full loop against a live feed."""

    def __init__(self, dbs: CamelDbs, registry: StrategyRegistry, *,
                 feed: Callable[[str], MarketSnapshot],
                 executor: Optional[RealisticPaperExecutor] = None,
                 mode: str = "enforcing", phase: int = 0, now: Optional[str] = None):
        self.dbs = dbs
        self.registry = registry
        self.feed = feed
        self.executor = executor or RealisticPaperExecutor()
        self.mode = mode
        self.phase = phase
        self.now = now

    def run_tick(self, symbols: List[str], state: PortfolioState, *,
                 notional_per_trade: float = 500.0) -> SandboxTick:
        out = SandboxTick()

        def virtual_execute(action: Action):
            snap = self.feed(getattr(action, "symbol", None))
            if snap is None or not snap.ask:
                f = Fill(action.symbol, "buy", 0, 0, 0, 0, 0, FillStatus.REJECTED, "no live quote")
                out.fills.append(f); return "no_quote"
            qty = int(notional_per_trade // snap.ask)        # whole shares within the per-trade notional
            if qty < 1:
                f = Fill(action.symbol, "buy", 0, 0, 0, 0, 0, FillStatus.REJECTED, "notional < 1 share")
                out.fills.append(f); return "size_too_small"
            order = Order(action.symbol, "buy", qty, limit_price=snap.ask)   # marketable limit at the ask
            fill = self.executor.execute(order, snap, now=self.now or snap.as_of)
            out.fills.append(fill)
            return f"{fill.status.value}:{fill.filled_qty}@{fill.fill_price}"

        loop = AssembledLoop(self.dbs, broker_execute=virtual_execute, phase=self.phase)
        out.tick = run_strategy_tick(self.dbs, self.registry, state, symbols=symbols,
                                     loop=loop, notional_per_trade=notional_per_trade, mode=self.mode)

        # No-Edge protocol: if the loop traded nothing, decide the honest fallback (DCA vs Wait)
        if not out.tick.executed:
            out.no_edge = resolve_no_edge(edge_allowed=False, has_capital=state.cash_usd > 0).path
        return out

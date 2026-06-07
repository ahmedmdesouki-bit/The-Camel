"""
Strategy driver (S11.5) — the keystone that makes S9–S11 one system at runtime.

Until now each layer was built + tested in isolation: the S11 strategy registry, the S10 full Edge
Proof engine, and the S10.5 assembled loop only met inside tests. This driver connects them:

    Regime (S9) → StrategyRegistry.signals_for (S11) → StrategyMixer → for each candidate compute the
    FULL 17-check EdgeReport (S10, evaluate_signal_full) → AssembledLoop.run_tick (S10.5)

So at runtime the loop now runs *real strategy candidates* through the *full* Edge Proof — not v0 alone.
Everything downstream is unchanged: Edge Proof → Constitution → Budget → Approval → Act, all on paper.
The driver PROPOSES and orchestrates; it gates nothing itself.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from db.paths import CamelDbs
from guardrail.constitution import Action, ActionType, PortfolioState, Thesis
from trader.engine.edge_proof_v0 import _load_closes
from trader.engine.edge_proof import evaluate_signal_full, _sharia_status
from trader.strategies.base import StrategyContext
from trader.strategies.registry import StrategyRegistry
from trader.strategies.mixer import StrategyMixer
from loop.assembled import AssembledLoop, TickResult


def build_context(dbs: CamelDbs, symbols: List[str], *, cash_usd: float = 0.0,
                  holdings: Optional[Dict[str, float]] = None,
                  as_of: Optional[str] = None) -> StrategyContext:
    """Assemble a point-in-time StrategyContext from the governed DBs (regime + closes + Sharia status)."""
    regime = "UNKNOWN"
    try:
        from trader.regime.features import build_features
        from trader.regime.classifier import classify
        regime = classify(build_features(dbs, as_of=as_of)).regime.value
    except Exception:                                   # pragma: no cover - defensive
        pass
    closes = {s: _load_closes(dbs.market, s, as_of=as_of) for s in symbols}
    whitelist = {s: _sharia_status(dbs, s) for s in symbols}
    return StrategyContext(as_of=as_of, regime=regime, closes=closes, whitelist=whitelist,
                           holdings=holdings or {}, cash_usd=cash_usd)


def run_strategy_tick(dbs: CamelDbs, registry: StrategyRegistry, state: PortfolioState, *,
                      symbols: List[str], portfolio_id: Optional[str] = None,
                      mixer: Optional[StrategyMixer] = None, loop: Optional[AssembledLoop] = None,
                      notional_per_trade: float = 50.0, budget_usd: Optional[float] = None,
                      max_candidates: int = 5, mode: str = "enforcing",
                      as_of: Optional[str] = None) -> TickResult:
    """Drive one full governed tick from live strategy signals. Returns the assembled-loop TickResult."""
    # P2-F: shadow/non-enforcing Edge Proof passes the gate vacuously (it logs without blocking). That is
    # only safe for paper calibration — refuse it the moment real capital is in play (phase >= 1).
    _phase = getattr(loop, "phase", 0) if loop is not None else 0
    if _phase >= 1 and mode != "enforcing":
        raise ValueError(f"non-enforcing Edge Proof mode {mode!r} is refused at phase {_phase} (live)")
    ctx = build_context(dbs, symbols, cash_usd=state.cash_usd, holdings=state.positions, as_of=as_of)
    signals = registry.signals_for(ctx, portfolio_id=portfolio_id)
    blended = (mixer or StrategyMixer()).blend(signals, registry)

    candidates: List[Action] = []
    edge_reports: Dict[str, object] = {}
    for bc in blended[:max_candidates]:
        if bc.symbol in ("CASH", ""):
            continue
        er = evaluate_signal_full(
            dbs, bc.symbol, signal=(bc.theme or "blend"),
            signal_definition=f"blended:{'/'.join(sorted(bc.strategies))}",
            budget_usd=budget_usd, mode=mode, as_of=as_of)
        # synthesise the required ThesisCard fields from the signal (a real strategy supplies these)
        thesis = Thesis(invalidation="edge invalidated / Sharia drift",
                        profit_take="+15% or regime change", time_stop="90d")
        candidates.append(Action(ActionType.TRADE, symbol=bc.symbol, side="buy",
                                 notional_usd=notional_per_trade, thesis=thesis, mode="paper"))
        edge_reports[bc.symbol] = er

    loop = loop or AssembledLoop(dbs)
    return loop.run_tick(candidates, state, edge_reports)

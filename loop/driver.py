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


def _last_buy_at(dbs: CamelDbs, symbol: str) -> Optional[str]:
    """Most-recent filled BUY timestamp for `symbol` (orders table), or None — the DCA cadence anchor."""
    from db.sqlite import connection
    try:
        with connection(dbs.portfolio) as conn:
            row = conn.execute(
                "SELECT filled_at FROM orders WHERE symbol=? AND lower(side)='buy' AND status='filled' "
                "ORDER BY id DESC LIMIT 1", (symbol,)).fetchone()
        return row[0] if row and row[0] else None
    except Exception:
        return None


def _within_days(ts: str, now_iso: str, days: float) -> bool:
    from datetime import datetime, timezone

    def _p(s):
        d = datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    try:
        return (_p(now_iso) - _p(ts)).total_seconds() < days * 86400.0
    except Exception:
        return False


def run_strategy_tick(dbs: CamelDbs, registry: StrategyRegistry, state: PortfolioState, *,
                      symbols: List[str], portfolio_id: Optional[str] = None,
                      mixer: Optional[StrategyMixer] = None, loop: Optional[AssembledLoop] = None,
                      notional_per_trade: float = 50.0, budget_usd: Optional[float] = None,
                      max_candidates: int = 5, mode: str = "enforcing",
                      as_of: Optional[str] = None, dca_cadence_days: float = 1.0) -> TickResult:
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
    meta: Dict[str, dict] = {}
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
        # carry the proposing strategies so the Measure step (S16) can attribute the outcome
        meta[bc.symbol] = {"strategies": sorted(bc.strategies), "theme": bc.theme or "blend"}

    loop = loop or AssembledLoop(dbs)
    result = loop.run_tick(candidates, state, edge_reports)

    # No-Edge → DCA fallback (S17): if the loop traded nothing on a proven edge but capital is idle, the
    # honest default is mechanical DCA into the compliant core — edge-EXEMPT (it's the benchmark, not a
    # bet). This NEVER resurrects a rejected alpha candidate: it deploys ONLY into the core ETF(s) the
    # `core_dca` strategy named, and the Constitution stays the Sharia/risk wall inside `run_dca`. The
    # decision itself is delegated to the S12 protocol fn (resolve_no_edge) so there is one source of truth:
    # edge proven → active strategy (no DCA); no edge + capital → DCA; no edge + no capital → wait.
    if not result.halted and not result.executed:
        from trader.edgelab.no_edge import resolve_no_edge, DCA_FALLBACK
        edge_proven = (result.router_path == "trader")     # the router only picks 'trader' on proven edge
        if resolve_no_edge(edge_allowed=edge_proven, has_capital=state.cash_usd > 0).path == DCA_FALLBACK:
            dca_actions: List[Action] = []
            seen = set()
            from datetime import datetime as _dt, timezone as _tz
            _ref_now = as_of or _dt.now(_tz.utc).isoformat()
            for sig in signals:
                if (getattr(sig, "strategy_id", "") == "core_dca"
                        and str(getattr(sig, "action", "")).lower() == "buy"
                        and sig.symbol not in seen):
                    seen.add(sig.symbol)
                    # DCA cadence: don't re-accumulate into a name already bought within the window.
                    # Default 1 day -> at most one DCA per name per day (stops a sub-daily loop from
                    # DCA-ing every tick); raise dca_cadence_days to ~28 for true monthly DCA.
                    _last = _last_buy_at(dbs, sig.symbol)
                    if _last is not None and _within_days(_last, _ref_now, dca_cadence_days):
                        continue
                    thesis = Thesis(invalidation="removed from the compliant core / Sharia drift",
                                    profit_take="long-term accumulation (no profit target)",
                                    time_stop="none - perpetual DCA")
                    dca_actions.append(Action(ActionType.TRADE, symbol=sig.symbol, side="buy",
                                              notional_usd=notional_per_trade, thesis=thesis, mode="paper"))
                    # attribute the fill to core_dca so the Measure step (S16) tracks its base-rate
                    meta[sig.symbol] = {"strategies": ["core_dca"], "theme": "core", "dca": True}
            if dca_actions:
                dca_outcomes = loop.run_dca(dca_actions, state)
                result.outcomes.extend(dca_outcomes)
                if any(o.stage == "executed" and o.approved for o in dca_outcomes):
                    result.router_path = "dca"
                    result.router_reason = "no proven edge + idle capital -> DCA into the compliant core"

    result.candidate_meta = meta
    return result

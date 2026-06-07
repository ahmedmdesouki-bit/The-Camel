"""Edge Lab (S12) — honest, cost-aware backtesting with a two-engine cross-check + the No-Edge protocol."""
from trader.edgelab.backtest import (
    BacktestResult, run_backtest, run_event_driven, run_vectorized, max_drawdown,
)
from trader.edgelab.honest import (
    walk_forward_split, survives_out_of_sample, passes_crisis, CRISIS_WINDOWS,
)
from trader.edgelab.no_edge import resolve_no_edge, beats_dca, NoEdgeDecision, DCA_FALLBACK

__all__ = [
    "BacktestResult", "run_backtest", "run_event_driven", "run_vectorized", "max_drawdown",
    "walk_forward_split", "survives_out_of_sample", "passes_crisis", "CRISIS_WINDOWS",
    "resolve_no_edge", "beats_dca", "NoEdgeDecision", "DCA_FALLBACK",
]

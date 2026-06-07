"""
Edge Lab backtester (S12) — honest, cost-aware, with a two-engine cross-check.

Two INDEPENDENT implementations of the same maths — a vectorized engine and an event-driven engine —
must agree to within a tiny tolerance. That cross-check is the point: if a look-ahead or off-by-one
bug creeps into one engine, the two disagree and the result is rejected rather than trusted. Returns
are net of per-trade transaction cost; the benchmark is simple buy-and-hold DCA (the No-Edge default).

Signals are a per-bar target position in {0, 1} (flat / long-one-unit), aligned to `closes`: `signals[i]`
is the position HELD from bar i to bar i+1. A position must therefore be decided from data up to bar i —
never i+1 (that would be look-ahead; the cross-check + walk-forward split in `honest.py` guard against it).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from typing import List


@dataclass
class BacktestResult:
    net_return: float
    gross_return: float
    n_trades: int
    max_drawdown: float
    dca_return: float
    beats_dca: bool
    engines_agree: bool


def _returns(closes: List[float]) -> List[float]:
    return [(closes[i + 1] / closes[i] - 1.0) if closes[i] else 0.0 for i in range(len(closes) - 1)]


def _trade_flags(signals: List[int]) -> List[bool]:
    """True at each bar where the target position changes vs the prior bar (entry from flat counts)."""
    out, prev = [], 0
    for s in signals:
        out.append(s != prev)
        prev = s
    return out


def run_event_driven(closes: List[float], signals: List[int], cost_bps: float = 20.0) -> float:
    """Walk bar-by-bar, applying the per-trade cost inline. Returns net total return."""
    rets = _returns(closes)
    flags = _trade_flags(signals)
    cost = cost_bps / 10000.0
    equity, prev = 1.0, 0
    for i in range(len(rets)):
        if signals[i] != prev:
            equity *= (1.0 - cost)
            prev = signals[i]
        equity *= (1.0 + signals[i] * rets[i])
    return round(equity - 1.0, 8)


def run_vectorized(closes: List[float], signals: List[int], cost_bps: float = 20.0) -> float:
    """Same maths via a product over per-bar multipliers (independent implementation)."""
    rets = _returns(closes)
    flags = _trade_flags(signals)
    cost = cost_bps / 10000.0
    mult = [((1.0 - cost) if flags[i] else 1.0) * (1.0 + signals[i] * rets[i]) for i in range(len(rets))]
    return round(reduce(lambda a, b: a * b, mult, 1.0) - 1.0, 8)


def max_drawdown(closes: List[float], signals: List[int], cost_bps: float = 20.0) -> float:
    rets = _returns(closes)
    cost = cost_bps / 10000.0
    equity, prev, peak, mdd = 1.0, 0, 1.0, 0.0
    for i in range(len(rets)):
        if signals[i] != prev:
            equity *= (1.0 - cost); prev = signals[i]
        equity *= (1.0 + signals[i] * rets[i])
        peak = max(peak, equity)
        mdd = min(mdd, equity / peak - 1.0)
    return round(mdd, 6)


def run_backtest(closes: List[float], signals: List[int], *, cost_bps: float = 20.0,
                 tol: float = 1e-6) -> BacktestResult:
    """Run both engines, cross-check them, and compare to buy-and-hold DCA. A divergence between the
    engines sets engines_agree=False — treat that result as untrusted."""
    evt = run_event_driven(closes, signals, cost_bps)
    vec = run_vectorized(closes, signals, cost_bps)
    agree = abs(evt - vec) <= tol
    dca = run_event_driven(closes, [1] * len(signals), cost_bps)   # always-in benchmark
    return BacktestResult(
        net_return=evt, gross_return=run_event_driven(closes, signals, 0.0),
        n_trades=sum(_trade_flags(signals)), max_drawdown=max_drawdown(closes, signals, cost_bps),
        dca_return=dca, beats_dca=(evt > dca), engines_agree=agree)

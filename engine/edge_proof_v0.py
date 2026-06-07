"""
Edge Proof v0 (S4.5) — the evidence gate, pulled forward.

The full 13-check Edge Proof Engine lands in S7. v0 is the cheapest first filter: using only
the price data already in camel_market.db, it proves a signal has basic historical support
versus a benchmark after estimated cost. No macro / fundamentals / news needed.

Hard rule: NO trade proceeds without an EdgeReport, and every missing/weak/stale input
defaults to trade_allowed=False. `gate()` is what the allocator calls.
"""
from __future__ import annotations
from dataclasses import dataclass
from statistics import median
from typing import List, Optional, Tuple

from db.sqlite import connection

DEFAULT_MIN_SAMPLE = 20
DEFAULT_HORIZON = 21        # ~one month of trading days
DEFAULT_COST = 0.002        # 0.2% round-trip cost estimate
DEFAULT_BENCHMARK = "SPUS_DCA"


@dataclass
class EdgeReport:
    symbol: str
    signal: str
    sample_size: int
    hit_rate: float
    median_forward_return: float
    worst_forward_return: float
    max_drawdown: float
    benchmark: str
    benchmark_excess_return: float
    confidence: float
    trade_allowed: bool
    reason: str


def compute_forward_returns(closes: List[float], horizon: int) -> List[float]:
    """Pure: forward return at each point = close[i+horizon]/close[i] - 1."""
    out: List[float] = []
    for i in range(len(closes) - horizon):
        base = closes[i]
        if base:
            out.append(closes[i + horizon] / base - 1.0)
    return out


def _max_drawdown(returns: List[float]) -> float:
    """Worst peak-to-trough on the equity curve built from sequential returns (<= 0)."""
    equity = peak = 1.0
    mdd = 0.0
    for r in returns:
        equity *= (1.0 + r)
        peak = max(peak, equity)
        mdd = min(mdd, equity / peak - 1.0)
    return mdd


def build_edge_report(
    symbol: str,
    signal: str,
    forward_returns: List[float],
    benchmark_return: Optional[float],
    benchmark: str = DEFAULT_BENCHMARK,
    estimated_cost: float = DEFAULT_COST,
    min_sample: int = DEFAULT_MIN_SAMPLE,
    data_fresh: bool = True,
) -> EdgeReport:
    """Pure: turn a set of forward returns + a benchmark into a gated EdgeReport."""
    n = len(forward_returns)
    if n == 0:
        return EdgeReport(symbol, signal, 0, 0.0, 0.0, 0.0, 0.0, benchmark,
                          0.0, 0.0, False, "no sample")

    hit = sum(1 for r in forward_returns if r > 0) / n
    med = median(forward_returns)
    worst = min(forward_returns)
    mdd = _max_drawdown(forward_returns)
    excess = med - benchmark_return if benchmark_return is not None else 0.0
    net = excess - estimated_cost
    confidence = round(min(1.0, n / min_sample) * hit, 3)

    reasons: List[str] = []
    allow = True
    if not data_fresh:
        allow = False; reasons.append("stale data")
    if n < min_sample:
        allow = False; reasons.append(f"sample too small ({n} < {min_sample})")
    if benchmark_return is None:
        allow = False; reasons.append("no benchmark")
    if benchmark_return is not None and net <= 0:
        allow = False; reasons.append("excess return weak after cost")

    return EdgeReport(
        symbol=symbol, signal=signal, sample_size=n, hit_rate=round(hit, 3),
        median_forward_return=round(med, 4), worst_forward_return=round(worst, 4),
        max_drawdown=round(mdd, 4), benchmark=benchmark,
        benchmark_excess_return=round(excess, 4), confidence=confidence,
        trade_allowed=allow, reason="; ".join(reasons) or "edge confirmed",
    )


def _load_closes(market_db: str, symbol: str, as_of: Optional[str] = None) -> List[float]:
    """Closes for a symbol, oldest→newest. **Point-in-time (P1-B):** pass `as_of` to see only bars
    whose session date ≤ as_of AND that Camel was already allowed to use (`known_at` ≤ as_of, or
    unset). With `as_of=None` (the live default) the behaviour is unchanged. This stops a backfill,
    sandbox replay, or restated/adjusted bar from leaking look-ahead into the trade verdict."""
    sql = "SELECT close FROM prices WHERE symbol=?"
    args: list = [symbol]
    if as_of is not None:
        sql += " AND date <= ? AND (known_at IS NULL OR known_at <= ?)"
        args += [as_of, as_of]
    sql += " ORDER BY date ASC"
    with connection(market_db) as conn:
        rows = conn.execute(sql, args).fetchall()
    return [r[0] for r in rows if r[0] is not None]


def evaluate_signal(
    market_db: str,
    symbol: str,
    signal: str,
    horizon: int = DEFAULT_HORIZON,
    benchmark_symbol: Optional[str] = None,
    estimated_cost: float = DEFAULT_COST,
    min_sample: int = DEFAULT_MIN_SAMPLE,
    data_fresh: bool = True,
    as_of: Optional[str] = None,
) -> EdgeReport:
    """
    Read prices from camel_market.db, compute the signal's forward-return distribution, and
    compare to the benchmark's median forward return over the same horizon. `as_of` (P1-B) enforces
    point-in-time honesty on both the symbol and the benchmark series.
    """
    closes = _load_closes(market_db, symbol, as_of=as_of)
    fwd = compute_forward_returns(closes, horizon)

    benchmark_return: Optional[float] = None
    benchmark = DEFAULT_BENCHMARK
    if benchmark_symbol:
        bench_fwd = compute_forward_returns(_load_closes(market_db, benchmark_symbol, as_of=as_of), horizon)
        benchmark = f"{benchmark_symbol}_BH"
        benchmark_return = median(bench_fwd) if bench_fwd else None

    return build_edge_report(symbol, signal, fwd, benchmark_return, benchmark,
                             estimated_cost, min_sample, data_fresh)


def gate(edge_report: Optional[EdgeReport]) -> Tuple[bool, str]:
    """
    The allocator's edge gate. No report at all = blocked. A report that is not trade_allowed
    = blocked with its reason. Only a passing report proceeds.
    """
    if edge_report is None:
        return False, "no edge proof"
    if not edge_report.trade_allowed:
        return False, edge_report.reason
    return True, "edge ok"


def log_edge_report(learning_db: str, report: EdgeReport) -> None:
    """Append the edge decision to the learning ledger (audit trail)."""
    import json
    with connection(learning_db) as conn:
        conn.execute(
            "INSERT INTO learning_ledger "
            "(decision_type, thesis_summary, expected_outcome, ref) VALUES (?,?,?,?)",
            ("EDGE_PROOF", f"{report.symbol}:{report.signal}",
             json.dumps(report.__dict__), report.symbol),
        )

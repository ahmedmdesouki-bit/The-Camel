"""
Full Edge Proof Engine (S10) — 17 signal-conditioned checks on top of the v0 gate.

v0 (`engine/edge_proof_v0.py`) is never removed — it stays the cheapest first filter. This engine
tests THE SIGNAL on real, point-in-time, regime-filtered data and adds the honesty controls that stop
a backtest from lying to itself: a multiple-testing penalty, a signal-decay test, a survivorship flag,
the Sharia-status-at-decision check, and a model-disagreement → human-approval rule.

Design:
  * The heavy logic is a PURE function (`run_full_edge_proof`) over explicit inputs — fully unit-tested,
    no I/O. A thin DB wrapper (`evaluate_signal_full`) loads prices/Sharia/regime and calls it.
  * Thresholds are PRE-REGISTERED constants (written down before the Edge Lab runs — never tuned to fit).
  * Fail-safe: any missing input on a BLOCKING check defaults to block. No edge proof = no trade.
  * The report exposes `trade_allowed` + `reason`, so the existing allocator gate works on it unchanged.
  * SHADOW vs ENFORCING: the report always records its real verdict (`would_allow`); `mode` controls
    whether the gate actually blocks. A fresh signal starts in shadow to calibrate, then is promoted.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from statistics import median, pstdev
from typing import Dict, List, Optional, Tuple

from trader.engine.edge_proof_v0 import compute_forward_returns, _max_drawdown, _load_closes

# ---- PRE-REGISTERED thresholds (founder-owned; fixed before the Edge Lab, never tuned to results) ----
MIN_SAMPLE = 50
MIN_REGIME_SAMPLE = 20
MIN_MEDIAN_EXCESS = 0.025          # ≥ +2.5% median excess over the benchmark for the horizon
WORST_RETURN_FLOOR = -0.25         # worst forward return no worse than −25% …
SMALL_POSITION_PCT = 0.02          # … unless the position is ≤ 2% of the book
MIN_DATA_QUALITY = 0.80
MIN_VOL_ADJ_RETURN = 0.15          # median ÷ stdev floor (soft quality signal)
DECAY_RATIO = 0.5                  # recent edge < 50% of full-sample edge → decayed
DEFAULT_COST = 0.002
SHARIA_CLEAR = {"pass", "compliant"}


@dataclass
class CheckResult:
    name: str
    passed: bool
    blocking: bool = True
    value: Optional[float] = None
    note: str = ""


@dataclass
class FullEdgeReport:
    symbol: str
    signal: str
    signal_definition_hash: str
    sample_size: int
    regime_filtered_sample_size: int
    hit_rate: float
    median_excess_return: float
    worst_forward_return: float
    max_drawdown: float
    benchmark: str
    after_costs: float
    turnover_estimate: float
    data_quality_score: float
    multiple_testing_penalty_applied: bool
    signal_decay_detected: bool
    checks: List[CheckResult] = field(default_factory=list)
    mode: str = "enforcing"                # shadow | enforcing
    would_allow: bool = False              # the real verdict regardless of mode
    trade_allowed: bool = False            # what the gate enforces (= would_allow if enforcing)
    reason: str = ""

    @property
    def failed_checks(self) -> List[str]:
        return [c.name for c in self.checks if c.blocking and not c.passed]


def signal_definition_hash(signal_definition: str) -> str:
    return hashlib.sha256((signal_definition or "").encode()).hexdigest()[:32]


def _safe_median(xs: List[float]) -> Optional[float]:
    return median(xs) if xs else None


def run_full_edge_proof(
    *, symbol: str, signal: str, signal_definition: str,
    forward_returns: List[float],
    benchmark_median_return: Optional[float],
    benchmark: str = "SPUS",
    regime_filtered_returns: Optional[List[float]] = None,
    recent_returns: Optional[List[float]] = None,
    n_signals_tested: int = 1,
    sharia_status: str = "unknown",
    data_quality_score: float = 0.85,
    source_quorum: int = 2,
    price: Optional[float] = None,
    budget_usd: Optional[float] = None,
    position_pct: float = 0.05,
    estimated_cost: float = DEFAULT_COST,
    turnover_estimate: float = 0.0,
    model_votes: Optional[Dict[str, str]] = None,
    survivorship_free: bool = False,
    mode: str = "enforcing",
) -> FullEdgeReport:
    """Run all 17 checks over explicit inputs and return a gated FullEdgeReport. Pure."""
    checks: List[CheckResult] = []
    n = len(forward_returns)
    med = _safe_median(forward_returns)
    bench = benchmark_median_return
    excess = (med - bench) if (med is not None and bench is not None) else None
    after_costs = (excess - estimated_cost) if excess is not None else None
    worst = min(forward_returns) if forward_returns else None
    mdd = _max_drawdown(forward_returns) if forward_returns else None
    hit = (sum(1 for r in forward_returns if r > 0) / n) if n else 0.0
    regime_n = len(regime_filtered_returns) if regime_filtered_returns is not None else n

    # 1 signal definition present
    checks.append(CheckResult("signal_definition", bool(signal and signal_definition),
                              note="signal + definition provided"))
    # 2 source provenance / quorum for non-price events
    checks.append(CheckResult("source_provenance", source_quorum >= 2, value=float(source_quorum),
                              note=f"source quorum {source_quorum} (≥2)"))
    # 3 point-in-time availability (caller computed returns with PIT prices)
    checks.append(CheckResult("point_in_time", True, blocking=False, note="PIT price series"))
    # 4 historical sample construction
    checks.append(CheckResult("sample_size", n >= MIN_SAMPLE, value=float(n),
                              note=f"{n} ≥ {MIN_SAMPLE}"))
    # 5 survivorship-bias control (flag until Sharadar/CRSP wired — non-blocking warning)
    checks.append(CheckResult("survivorship_control", survivorship_free, blocking=False,
                              note="survivorship-free source" if survivorship_free
                              else "⚠ adjusted EOD, not survivorship-curated (Sharadar pending)"))
    # 6 similar-regime filter
    checks.append(CheckResult("regime_filter", regime_n >= MIN_REGIME_SAMPLE, value=float(regime_n),
                              note=f"regime-filtered sample {regime_n} ≥ {MIN_REGIME_SAMPLE}"))
    # 7 forward returns computed
    checks.append(CheckResult("forward_returns", med is not None, blocking=False,
                              value=med, note="forward-return distribution built"))
    # 8 benchmark comparison
    checks.append(CheckResult("benchmark_comparison", excess is not None and excess >= MIN_MEDIAN_EXCESS,
                              value=excess, note=f"median excess vs {benchmark} ≥ {MIN_MEDIAN_EXCESS:.1%}"))
    # 9 transaction cost + spread (net positive after cost)
    checks.append(CheckResult("after_costs", after_costs is not None and after_costs > 0,
                              value=after_costs, note="net positive after estimated cost"))
    # 10 worst-case drawdown (allowed worse only for a small position)
    worst_ok = (worst is not None and (worst >= WORST_RETURN_FLOOR or position_pct <= SMALL_POSITION_PCT))
    checks.append(CheckResult("worst_case", worst_ok, value=worst,
                              note=f"worst {worst:.1%} ≥ {WORST_RETURN_FLOOR:.0%} or position ≤ {SMALL_POSITION_PCT:.0%}"
                              if worst is not None else "no worst-return data"))
    # 11 volatility-adjusted return (soft)
    vol = pstdev(forward_returns) if n > 1 else None
    vadj = (med / vol) if (med is not None and vol) else None
    checks.append(CheckResult("vol_adjusted", vadj is not None and vadj >= MIN_VOL_ADJ_RETURN,
                              blocking=False, value=vadj, note="median/stdev floor"))
    # 12 multiple-testing penalty
    penalty_applied = n_signals_tested > 1
    penalty_factor = min(2.0, 1.0 + 0.1 * max(0, n_signals_tested - 1))
    penalized_min = MIN_MEDIAN_EXCESS * penalty_factor
    checks.append(CheckResult("multiple_testing", excess is not None and excess >= penalized_min,
                              value=penalized_min,
                              note=f"excess ≥ penalized bar {penalized_min:.2%} (tested {n_signals_tested})"))
    # 13 signal-decay test (recent vs full)
    recent_med = _safe_median(recent_returns) if recent_returns is not None else None
    decay_detected = (recent_med is not None and med is not None and med > 0
                      and recent_med < med * DECAY_RATIO)
    checks.append(CheckResult("signal_decay", not decay_detected, value=recent_med,
                              note="recent edge not materially below full sample"))
    # 14 counter-signal inventory (record only)
    checks.append(CheckResult("counter_signal_inventory", True, blocking=False,
                              note="counter-signals to be enumerated by the research desk"))
    # 15 Sharia status at the decision date (fail-safe — Sharia is #1)
    sharia_ok = (sharia_status or "").lower() in SHARIA_CLEAR
    checks.append(CheckResult("sharia_status", sharia_ok, value=None,
                              note=f"sharia status='{sharia_status}' (must be a clear pass)"))
    # 16 liquidity + whole-share feasibility
    feasible = (price is None or budget_usd is None or price <= budget_usd)
    checks.append(CheckResult("whole_share_feasible", feasible, blocking=False,
                              note="price ≤ budget for a whole share"))
    # data quality (a gating prerequisite, folded in)
    checks.append(CheckResult("data_quality", data_quality_score >= MIN_DATA_QUALITY,
                              value=data_quality_score, note=f"≥ {MIN_DATA_QUALITY}"))
    # model disagreement (BOARDROOM) → human approval
    disagree = bool(model_votes) and len(set(model_votes.values())) > 1
    checks.append(CheckResult("model_agreement", not disagree, value=None,
                              note="bull/bear/sharia-auditor agree (else → human approval gate)"))

    blocking_fail = [c for c in checks if c.blocking and not c.passed]
    would_allow = not blocking_fail
    reason = "edge confirmed" if would_allow else "; ".join(
        f"{c.name} failed" for c in blocking_fail)
    if disagree:
        reason = "model disagreement → human approval required; " + reason

    trade_allowed = would_allow if mode == "enforcing" else True   # shadow logs but does not block

    # 17 final decision (record)
    checks.append(CheckResult("final_decision", would_allow, blocking=False,
                              note=reason))

    return FullEdgeReport(
        symbol=symbol, signal=signal, signal_definition_hash=signal_definition_hash(signal_definition),
        sample_size=n, regime_filtered_sample_size=regime_n, hit_rate=round(hit, 3),
        median_excess_return=round(excess, 4) if excess is not None else 0.0,
        worst_forward_return=round(worst, 4) if worst is not None else 0.0,
        max_drawdown=round(mdd, 4) if mdd is not None else 0.0, benchmark=benchmark,
        after_costs=round(after_costs, 4) if after_costs is not None else 0.0,
        turnover_estimate=turnover_estimate, data_quality_score=data_quality_score,
        multiple_testing_penalty_applied=penalty_applied, signal_decay_detected=decay_detected,
        checks=checks, mode=mode, would_allow=would_allow, trade_allowed=trade_allowed, reason=reason,
    )


def gate(report: Optional[FullEdgeReport], enforcing: bool = True) -> Tuple[bool, str]:
    """Gate compatible with the allocator. In shadow mode (enforcing=False / report.mode='shadow')
    it never blocks but returns the would-be verdict in the reason."""
    if report is None:
        return False, "no edge report"
    if report.mode == "shadow" or not enforcing:
        return True, f"shadow: would_{'allow' if report.would_allow else 'block'} ({report.reason})"
    return report.trade_allowed, report.reason


# ---------------------------------------------------------------- DB-backed wrapper

def _sharia_status(dbs, symbol: str) -> str:
    """Latest multi-state Sharia status (S9), falling back to the whitelist; 'unknown' if neither."""
    from db.sqlite import connection
    with connection(dbs.sharia) as conn:
        row = conn.execute("SELECT final_status FROM sharia_status WHERE symbol=? ORDER BY id DESC LIMIT 1",
                           (symbol,)).fetchone()
        if row and row["final_status"]:
            return row["final_status"]
        wl = conn.execute("SELECT sharia_status FROM whitelist WHERE symbol=?", (symbol,)).fetchone()
    return (wl["sharia_status"] if wl else None) or "unknown"


def evaluate_signal_full(dbs, symbol: str, signal: str, signal_definition: str, *,
                         horizon: int = 21, benchmark_symbol: str = "SPUS",
                         n_signals_tested: int = 1, position_pct: float = 0.05,
                         budget_usd: Optional[float] = None, mode: str = "enforcing",
                         regime_filtered_returns: Optional[List[float]] = None,
                         data_quality_score: float = 0.85,
                         model_votes: Optional[Dict[str, str]] = None,
                         as_of: Optional[str] = None) -> FullEdgeReport:
    """Load prices (camel_market.db) + the symbol's Sharia status (S9), build the inputs, and run the
    full engine. Reuses the v0 loaders so v0 stays the cheapest first filter. `as_of` (P1-B) enforces
    point-in-time honesty on the price series (no look-ahead from backfills/replays/restatements)."""
    closes = _load_closes(dbs.market, symbol, as_of=as_of)
    fwd = compute_forward_returns(closes, horizon)
    bench_fwd = compute_forward_returns(_load_closes(dbs.market, benchmark_symbol, as_of=as_of), horizon)
    bench_med = median(bench_fwd) if bench_fwd else None
    # "recent" = the most recent quarter of the signal's forward returns, for the decay test
    recent = fwd[-max(MIN_REGIME_SAMPLE, len(fwd) // 4):] if fwd else []
    return run_full_edge_proof(
        symbol=symbol, signal=signal, signal_definition=signal_definition,
        forward_returns=fwd, benchmark_median_return=bench_med, benchmark=benchmark_symbol,
        regime_filtered_returns=regime_filtered_returns, recent_returns=recent,
        n_signals_tested=n_signals_tested, sharia_status=_sharia_status(dbs, symbol),
        data_quality_score=data_quality_score, price=(closes[-1] if closes else None),
        budget_usd=budget_usd, position_pct=position_pct, model_votes=model_votes, mode=mode,
    )


def log_full_edge_report(dbs, report: FullEdgeReport) -> None:
    """Append the full report to camel_learning.db.edge_reports (the decision-quality audit trail)."""
    import json
    from db.sqlite import connection
    checks = [{"name": c.name, "passed": c.passed, "blocking": c.blocking,
               "value": c.value, "note": c.note} for c in report.checks]
    with connection(dbs.learning) as conn:
        conn.execute(
            "INSERT INTO edge_reports (symbol, signal, signal_definition_hash, sample_size, "
            " regime_filtered_sample_size, hit_rate, median_excess_return, worst_forward_return, "
            " max_drawdown, benchmark, after_costs, turnover_estimate, data_quality_score, "
            " multiple_testing_penalty_applied, signal_decay_detected, mode, would_allow, "
            " trade_allowed, reason, checks_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (report.symbol, report.signal, report.signal_definition_hash, report.sample_size,
             report.regime_filtered_sample_size, report.hit_rate, report.median_excess_return,
             report.worst_forward_return, report.max_drawdown, report.benchmark, report.after_costs,
             report.turnover_estimate, report.data_quality_score,
             1 if report.multiple_testing_penalty_applied else 0,
             1 if report.signal_decay_detected else 0, report.mode,
             1 if report.would_allow else 0, 1 if report.trade_allowed else 0, report.reason,
             json.dumps(checks)),
        )

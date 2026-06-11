"""
Edge Lab run harness (S16) — one command that answers the only question that matters:

    python -m trader.edgelab.run --symbols SPUS,HLAL          # → EDGE or NO_EDGE→DCA, per symbol

It pulls REAL closes from camel_market.db (point-in-time loader), generates per-bar signals from a
named rule, and runs the full honesty stack: the two-engine cross-checked backtest (net of costs),
the walk-forward out-of-sample survival guard, the beats-DCA bar, and the No-Edge protocol. The
verdict is the system's own philosophy applied to itself: an active strategy runs ONLY if it proves
an edge out-of-sample AND beats simple DCA after costs — otherwise the humble answer is DCA, which
is a SUCCESS state, not a failure.

Signal rules honour the backtester's contract: `signals[i]` (the position held from bar i to i+1)
is computed from closes[0..i] only — never bar i+1.
"""
from __future__ import annotations

import json
import os
from typing import Callable, Dict, List, Optional

from trader.engine.edge_proof_v0 import _load_closes
from trader.edgelab.backtest import run_backtest
from trader.edgelab.honest import survives_out_of_sample, walk_forward_split
from trader.edgelab.no_edge import resolve_no_edge

MIN_BARS = 120                      # below this, no honest verdict is possible


def sma_trend_signals(closes: List[float], n: int = 50) -> List[int]:
    """Long when the close sits above its n-bar simple moving average (data up to bar i only)."""
    out: List[int] = []
    for i in range(len(closes)):
        window = closes[max(0, i - n + 1): i + 1]
        sma = sum(window) / len(window)
        out.append(1 if closes[i] > sma else 0)
    return out


def momentum_signals(closes: List[float], lookback: int = 63) -> List[int]:
    """Long when the close exceeds its level `lookback` bars ago (~12-1 style time-series momentum)."""
    return [1 if i >= lookback and closes[i] > closes[i - lookback] else 0
            for i in range(len(closes))]


RULES: Dict[str, Callable[[List[float]], List[int]]] = {
    "sma_trend": sma_trend_signals,
    "momentum": momentum_signals,
}


def evaluate_symbol(market_db: str, symbol: str, *, rule: str = "sma_trend",
                    cost_bps: float = 20.0, train_frac: float = 0.7,
                    as_of: Optional[str] = None) -> dict:
    """The full honesty stack for one symbol+rule. Returns a verdict dict (never raises on thin data)."""
    closes = _load_closes(market_db, symbol, as_of=as_of)
    if len(closes) < MIN_BARS:
        return {"symbol": symbol, "rule": rule, "verdict": "insufficient_data",
                "bars": len(closes), "needed": MIN_BARS,
                "note": "no honest verdict from a thin sample — ingest more history first"}

    signals = RULES[rule](closes)
    train_idx, _test_idx = walk_forward_split(len(closes), train_frac)
    cut = len(train_idx)

    full = run_backtest(closes, signals, cost_bps=cost_bps)
    train = run_backtest(closes[:cut], signals[:cut], cost_bps=cost_bps)
    test = run_backtest(closes[cut:], signals[cut:], cost_bps=cost_bps)

    # Compare PER-BAR (geometric) returns, not raw segment totals: the 70/30 split means a perfectly
    # steady true edge tops out at a raw test/train ratio of ~0.43 — below the 0.5 survival bar — so
    # without normalization the EDGE verdict was mathematically unreachable (QA finding).
    def _per_bar(total: float, bars: int) -> float:
        return (1.0 + total) ** (1.0 / max(1, bars)) - 1.0 if total > -1.0 else -1.0

    oos_ok = survives_out_of_sample(_per_bar(train.net_return, max(1, cut - 1)),
                                    _per_bar(test.net_return, max(1, len(closes) - cut - 1)))
    engines_ok = full.engines_agree and train.engines_agree and test.engines_agree
    edge_allowed = oos_ok and engines_ok
    decision = resolve_no_edge(edge_allowed, has_capital=True, beats_dca=full.beats_dca)

    return {
        "symbol": symbol, "rule": rule, "bars": len(closes), "cost_bps": cost_bps,
        "net_return": full.net_return, "dca_return": full.dca_return,
        "beats_dca": full.beats_dca, "n_trades": full.n_trades,
        "max_drawdown": full.max_drawdown,
        "train_return": train.net_return, "test_return": test.net_return,
        "survives_out_of_sample": oos_ok, "engines_agree": engines_ok,
        "verdict": "EDGE" if decision.path == "active_strategy" else "NO_EDGE_DCA",
        "path": decision.path, "reason": decision.reason,
    }


def evaluate_universe(market_db: str, symbols: List[str], *, rule: str = "sma_trend",
                      cost_bps: float = 20.0, as_of: Optional[str] = None) -> List[dict]:
    return [evaluate_symbol(market_db, s, rule=rule, cost_bps=cost_bps, as_of=as_of)
            for s in symbols]


def _utf8_stdout() -> None:                                  # pragma: no cover - CLI cosmetic
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")             # Windows cp1252 console can't print →/—
    except Exception:
        pass


def main(argv=None) -> int:                                 # pragma: no cover - CLI entrypoint
    import argparse
    _utf8_stdout()
    p = argparse.ArgumentParser(description="The Camel — Edge Lab verdict on real history")
    p.add_argument("--symbols", default=os.environ.get("CAMEL_SYMBOLS", "SPUS,HLAL"))
    p.add_argument("--rule", default="sma_trend", choices=sorted(RULES))
    p.add_argument("--cost-bps", type=float, default=20.0)
    p.add_argument("--db-dir", default=os.environ.get("CAMEL_DB_DIR", "."))
    p.add_argument("--json-out", default="", help="optional path to write the full report as JSON")
    args = p.parse_args(argv)

    from db.paths import CamelDbs
    dbs = CamelDbs.from_dir(args.db_dir)
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    results = evaluate_universe(dbs.market, symbols, rule=args.rule, cost_bps=args.cost_bps)

    for r in results:
        if r["verdict"] == "insufficient_data":
            print(f"  {r['symbol']:<6} INSUFFICIENT DATA ({r['bars']}/{r['needed']} bars)")
        else:
            print(f"  {r['symbol']:<6} {r['verdict']:<12} net={r['net_return']:+.1%} "
                  f"dca={r['dca_return']:+.1%} oos={'ok' if r['survives_out_of_sample'] else 'FAIL'} "
                  f"trades={r['n_trades']}  → {r['reason']}")
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"report → {args.json_out}")
    return 0


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())

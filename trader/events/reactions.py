"""
Event-reaction substrate (S9 slice 3) — how markets REACTED to each enriched event.

For every (event, affected-symbol) pair it computes forward returns at 1/5/21/63/126 trading-day
horizons from the event date, the 63-day max drawdown, the same-horizon benchmark return + excess,
and the macro regime in force at the event — writing one point-in-time row to `event_reactions`.

IMPORTANT — this is a STUDY / base-rate table, not a live signal: the return_* columns are realized
with hindsight (computed after the window closed) and exist to power the S10 event studies ("when
this kind of event happened in this regime, what did the asset do next, vs the benchmark?"). It is
never read as a forward-looking trade signal. Pure math helpers (`forward_returns_from`,
`max_drawdown_window`) are side-effect-free and unit-tested.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from db.paths import CamelDbs
from db.sqlite import connection

HORIZONS = [1, 5, 21, 63, 126]
DEFAULT_BENCHMARK = "SPUS"
_DD_WINDOW = 63


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_series(market_db: str, symbol: str) -> List[Tuple[str, float]]:
    """[(date, close)] for a symbol, ascending by date, prefer adj_close, de-duplicated by date."""
    with connection(market_db) as conn:
        rows = conn.execute(
            "SELECT date, COALESCE(adj_close, close) AS px FROM prices "
            "WHERE symbol=? AND COALESCE(adj_close, close) IS NOT NULL ORDER BY date ASC",
            (symbol,),
        ).fetchall()
    out: List[Tuple[str, float]] = []
    seen = set()
    for r in rows:
        d = r["date"]
        if d in seen:
            continue
        seen.add(d)
        out.append((d, float(r["px"])))
    return out


def _entry_index(series: List[Tuple[str, float]], event_date: str) -> Optional[int]:
    """First bar on/after the event date (lexicographic ISO-date compare)."""
    key = (event_date or "")[:10]
    for i, (d, _) in enumerate(series):
        if d[:10] >= key:
            return i
    return None


def forward_returns_from(series: List[Tuple[str, float]], event_date: str,
                         horizons: List[int] = HORIZONS) -> Dict[int, Optional[float]]:
    """Pure: forward return at each horizon from the entry bar (first bar on/after event_date)."""
    out: Dict[int, Optional[float]] = {h: None for h in horizons}
    i = _entry_index(series, event_date)
    if i is None:
        return out
    base = series[i][1]
    if not base:
        return out
    for h in horizons:
        j = i + h
        if j < len(series):
            out[h] = round(series[j][1] / base - 1.0, 6)
    return out


def max_drawdown_window(series: List[Tuple[str, float]], event_date: str,
                        window: int = _DD_WINDOW) -> Optional[float]:
    """Pure: worst peak-to-trough (≤ 0) over `window` bars from the entry bar."""
    i = _entry_index(series, event_date)
    if i is None or i >= len(series):
        return None
    base = series[i][1]
    if not base:
        return None
    peak = 1.0
    mdd = 0.0
    end = min(i + window, len(series) - 1)
    for k in range(i, end + 1):
        eq = series[k][1] / base
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1.0)
    return round(mdd, 6)


def regime_at(dbs: CamelDbs, date: str) -> Optional[str]:
    """The macro regime classified at/before `date` (None if none recorded yet)."""
    try:
        with connection(dbs.macro) as conn:
            row = conn.execute(
                "SELECT regime FROM regime_history WHERE classified_at <= ? "
                "ORDER BY classified_at DESC LIMIT 1", (date,)).fetchone()
    except Exception:
        return None
    return row["regime"] if row else None


def compute_event_reaction(dbs: CamelDbs, *, event_id: str, event_type: str, symbol: str,
                           sector: str, event_date: str, known_at: str,
                           benchmark: str = DEFAULT_BENCHMARK) -> Optional[dict]:
    """Compute one reaction row. Returns None if the symbol has no usable price history at the event
    (no entry bar or not even a 1-day forward return) — so we never fabricate a reaction."""
    series = _load_series(dbs.market, symbol)
    rets = forward_returns_from(series, event_date)
    if rets.get(1) is None and all(rets.get(h) is None for h in HORIZONS):
        return None                                   # no usable forward return → skip
    bench_series = _load_series(dbs.market, benchmark) if benchmark else []
    bench_21 = forward_returns_from(bench_series, event_date, [21]).get(21) if bench_series else None
    sym_21 = rets.get(21)
    excess_21 = round(sym_21 - bench_21, 6) if (sym_21 is not None and bench_21 is not None) else None
    return {
        "event_id": event_id, "event_type": event_type, "symbol": symbol, "sector": sector,
        "event_date": event_date, "known_at": known_at,
        "return_1d": rets.get(1), "return_5d": rets.get(5), "return_21d": rets.get(21),
        "return_63d": rets.get(63), "return_126d": rets.get(126),
        "max_drawdown_63d": max_drawdown_window(series, event_date),
        "benchmark": benchmark, "benchmark_return_21d": bench_21, "excess_return_21d": excess_21,
        "regime_at_event": regime_at(dbs, event_date),
        "computed_at": _utcnow(),
    }


def record_event_reactions(dbs: CamelDbs, benchmark: str = DEFAULT_BENCHMARK, limit: int = 1000) -> int:
    """For every enriched, safe event × affected symbol with usable prices, compute + store one
    `event_reactions` row. Idempotent (UNIQUE(event_id, symbol) → INSERT OR IGNORE). Returns rows written."""
    from data.entity_resolver import resolve

    with connection(dbs.news) as conn:
        events = [dict(r) for r in conn.execute(
            "SELECT event_id, event_type, affected_assets, event_date, known_at FROM news_events "
            "WHERE safe=1 AND affected_assets IS NOT NULL AND affected_assets != '[]' "
            "ORDER BY id LIMIT ?", (limit,)).fetchall()]

    written = 0
    for ev in events:
        try:
            symbols = json.loads(ev.get("affected_assets") or "[]")
        except (ValueError, TypeError):
            symbols = []
        for symbol in symbols:
            sector = resolve(dbs, symbol).sector
            row = compute_event_reaction(
                dbs, event_id=ev["event_id"], event_type=ev.get("event_type"), symbol=symbol,
                sector=sector, event_date=ev["event_date"], known_at=ev.get("known_at"),
                benchmark=benchmark)
            if row is None:
                continue
            with connection(dbs.news) as conn:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO event_reactions "
                    "(event_id, event_type, symbol, sector, event_date, known_at, return_1d, return_5d, "
                    " return_21d, return_63d, return_126d, max_drawdown_63d, benchmark, "
                    " benchmark_return_21d, excess_return_21d, regime_at_event, computed_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (row["event_id"], row["event_type"], row["symbol"], row["sector"],
                     row["event_date"], row["known_at"], row["return_1d"], row["return_5d"],
                     row["return_21d"], row["return_63d"], row["return_126d"], row["max_drawdown_63d"],
                     row["benchmark"], row["benchmark_return_21d"], row["excess_return_21d"],
                     row["regime_at_event"], row["computed_at"]),
                )
                written += cur.rowcount
    return written

"""
Regime feature builder (S9) — assemble macro features from camel_macro.db.

Pulls the latest level of each configured FRED-style series from `macro_observations`, derives the
yield curve (10y − 2y), and computes year-over-year change for level series (CPI, oil). Missing series
return None — the classifier degrades gracefully rather than guessing. Point-in-time honest: it only
reads observations whose `event_date` ≤ `as_of`.
"""
from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

from db.sqlite import connection
from db.paths import CamelDbs
from trader.regime.peg import peg_status

# feature name → series_id as ingested by the FRED/Treasury/etc. connectors
DEFAULT_SERIES = {
    "fed_funds": "FEDFUNDS",
    "dgs2": "DGS2",
    "dgs10": "DGS10",
    "unemployment": "UNRATE",
    "hy_spread": "BAMLH0A0HYM2",
    "vix": "VIXCLS",
    "usd": "DTWEXBGS",
    "cpi": "CPIAUCSL",
    "oil": "DCOILWTICO",
    "usd_sar": "DEXSAUS",        # S9 slice 4: USD/SAR spot → the peg monitor (free, FRED)
    "gpr": "GPR",                # S17: Caldara-Iacoviello Geopolitical Risk Index (free, CC BY)
}


def _points(db: str, series_id: str, as_of: Optional[str]) -> List[Tuple[str, float]]:
    """Point-in-time, vintage-aware: only observations with event_date AND reported_at <= as_of,
    and for each event_date keep the LATEST vintage available as of that cutoff (no look-ahead)."""
    sql = "SELECT event_date, reported_at, value FROM macro_observations WHERE series_id=?"
    args: list = [series_id]
    if as_of:
        # Point-in-time (P2-A): the observation's session is past (event_date), its vintage was
        # published (reported_at), AND Camel was already allowed to use it (known_at — the usability
        # clock that an embargo/licence lag can push past reported_at). All three ≤ as_of.
        sql += (" AND event_date <= ? AND (reported_at IS NULL OR reported_at <= ?)"
                " AND (known_at IS NULL OR known_at <= ?)")
        args += [as_of, as_of, as_of]
    sql += " ORDER BY event_date, reported_at"        # ascending → last write per date = latest vintage
    latest_by_date: Dict[str, float] = {}
    with connection(db) as conn:
        for r in conn.execute(sql, args).fetchall():
            if r["value"] is not None:
                latest_by_date[r["event_date"]] = r["value"]
    return sorted(latest_by_date.items())


def _latest(points: List[Tuple[str, float]]) -> Optional[float]:
    return points[-1][1] if points else None


def _pdate(d: str) -> date:
    return date.fromisoformat(d[:10])


def _yoy(points: List[Tuple[str, float]], window_days: int = 60) -> Optional[float]:
    """True year-over-year % change: latest value vs the observation closest to exactly one year
    earlier (within `window_days`). Returns None if no point lands near the 1-year-ago mark — so a
    short series can't be mislabeled as YoY (the previous month-over-month bug)."""
    if len(points) < 2:
        return None
    latest_d, latest_v = points[-1]
    target = _pdate(latest_d) - timedelta(days=365)
    best_v, best_diff = None, None
    for d, v in points[:-1]:
        diff = abs((_pdate(d) - target).days)
        if best_diff is None or diff < best_diff:
            best_diff, best_v = diff, v
    if best_v is None or best_diff is None or best_diff > window_days or not best_v:
        return None
    return round((latest_v / best_v - 1.0) * 100.0, 2)


def build_features(dbs: CamelDbs, series: Dict[str, str] = None,
                   as_of: Optional[str] = None) -> Dict[str, Optional[float]]:
    series = series or DEFAULT_SERIES
    db = dbs.macro

    def pts(name):
        return _points(db, series[name], as_of) if name in series else []

    d2 = _latest(pts("dgs2"))
    d10 = _latest(pts("dgs10"))
    usd_sar = _latest(pts("usd_sar"))
    peg = peg_status(usd_sar)              # None rate → known=False → deviation None (peg feature dormant)
    return {
        "fed_funds": _latest(pts("fed_funds")),
        "yield_curve": (d10 - d2) if (d2 is not None and d10 is not None) else None,
        "unemployment": _latest(pts("unemployment")),
        "hy_spread": _latest(pts("hy_spread")),
        "vix": _latest(pts("vix")),
        "usd": _latest(pts("usd")),
        "cpi_yoy": _yoy(pts("cpi")),
        "oil_change_pct": _yoy(pts("oil")),
        "peg_deviation_pct": peg.get("deviation_pct"),   # USD/SAR drift vs the 3.75 peg
        "gpr": _latest(pts("gpr")),                      # geopolitical risk index level (baseline ~100)
    }

"""
Regime feature builder (S9) — assemble macro features from camel_macro.db.

Pulls the latest level of each configured FRED-style series from `macro_observations`, derives the
yield curve (10y − 2y), and computes year-over-year change for level series (CPI, oil). Missing series
return None — the classifier degrades gracefully rather than guessing. Point-in-time honest: it only
reads observations whose `event_date` ≤ `as_of`.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Tuple

from db.sqlite import connection
from db.paths import CamelDbs

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
}


def _points(db: str, series_id: str, as_of: Optional[str]) -> List[Tuple[str, float]]:
    sql = "SELECT event_date, value FROM macro_observations WHERE series_id=?"
    args: list = [series_id]
    if as_of:
        sql += " AND event_date <= ?"
        args.append(as_of)
    sql += " ORDER BY event_date"
    with connection(db) as conn:
        return [(r["event_date"], r["value"]) for r in conn.execute(sql, args).fetchall()
                if r["value"] is not None]


def _latest(points: List[Tuple[str, float]]) -> Optional[float]:
    return points[-1][1] if points else None


def _yoy(points: List[Tuple[str, float]]) -> Optional[float]:
    """Year-over-year % change of the latest point vs the point closest to ~1 year earlier."""
    if len(points) < 2:
        return None
    latest_date, latest_val = points[-1]
    target_year = str(int(latest_date[:4]) - 1)
    prior = None
    for d, v in points:                              # last point with year <= (latest_year - 1)
        if d[:4] <= target_year:
            prior = v
    if prior is None:
        prior = points[0][1]                         # fall back to earliest available
    if not prior:
        return None
    return round((latest_val / prior - 1.0) * 100.0, 2)


def build_features(dbs: CamelDbs, series: Dict[str, str] = None,
                   as_of: Optional[str] = None) -> Dict[str, Optional[float]]:
    series = series or DEFAULT_SERIES
    db = dbs.macro

    def pts(name):
        return _points(db, series[name], as_of) if name in series else []

    d2 = _latest(pts("dgs2"))
    d10 = _latest(pts("dgs10"))
    return {
        "fed_funds": _latest(pts("fed_funds")),
        "yield_curve": (d10 - d2) if (d2 is not None and d10 is not None) else None,
        "unemployment": _latest(pts("unemployment")),
        "hy_spread": _latest(pts("hy_spread")),
        "vix": _latest(pts("vix")),
        "usd": _latest(pts("usd")),
        "cpi_yoy": _yoy(pts("cpi")),
        "oil_change_pct": _yoy(pts("oil")),
    }

"""
SAR/USD peg monitor (S9 — harvested from Alaa's parallel build).

The founder is KSA-resident and the book is SAR-funded but USD-denominated (SCHD/SCHX on Sahm).
The Saudi riyal has been pegged at 3.75 SAR/USD since 1986, so under normal conditions there is
**no FX risk** — but a peg under stress would be a first-order macro event. This is a small,
pure macro primitive the regime engine (S9) can fold in as a feature/flag: peg intact ⇒ ignore
FX; peg drifting ⇒ surface it.

Pure function (`peg_status`) plus a defensive reader (`latest_peg_status`) that returns None when
no FX series has been ingested — so it is dormant-safe until a USDSAR feed exists.
"""
from __future__ import annotations

from typing import Optional

from db.paths import CamelDbs
from db.sqlite import connection

PEG_RATE = 3.75                 # official USD/SAR peg since 1986
DEFAULT_TOLERANCE_PCT = 0.5     # within ±0.5% of 3.75 → "intact"
DEFAULT_SERIES_ID = "USDSAR"


def peg_status(rate: Optional[float], peg: float = PEG_RATE,
               tolerance_pct: float = DEFAULT_TOLERANCE_PCT) -> dict:
    """Classify a USD/SAR rate against the peg. Pure — no I/O."""
    if rate is None or peg <= 0:
        return {"known": False, "intact": None, "rate": rate, "peg": peg,
                "deviation_pct": None, "note": "no USD/SAR observation available"}
    deviation_pct = (float(rate) - peg) / peg * 100.0
    intact = abs(deviation_pct) <= tolerance_pct
    note = ("peg intact — no FX risk" if intact
            else f"⚠ peg drift {deviation_pct:+.2f}% vs {peg} — surface as a macro risk")
    return {"known": True, "intact": intact, "rate": round(float(rate), 4), "peg": peg,
            "deviation_pct": round(deviation_pct, 3), "note": note}


def latest_peg_status(dbs: CamelDbs, series_id: str = DEFAULT_SERIES_ID,
                      tolerance_pct: float = DEFAULT_TOLERANCE_PCT,
                      as_of: Optional[str] = None) -> Optional[dict]:
    """Read the most recent USD/SAR observation (point-in-time) and classify it.

    Returns None if no such series has been ingested yet (dormant-safe). `as_of` (P3-E) makes this
    reusable in a backtest/as-of context: only observations Camel could already see (event_date and
    known_at ≤ as_of). With `as_of=None` (the live default) it reads the latest known observation."""
    sql = ("SELECT value, event_date FROM macro_observations "
           "WHERE series_id = ? AND value IS NOT NULL")
    args: list = [series_id]
    if as_of is not None:
        sql += " AND event_date <= ? AND (known_at IS NULL OR known_at <= ?)"
        args += [as_of, as_of]
    sql += " ORDER BY known_at DESC, id DESC LIMIT 1"
    try:
        with connection(dbs.macro) as conn:
            row = conn.execute(sql, args).fetchone()
    except Exception:
        return None
    if row is None:
        return None
    status = peg_status(row["value"], tolerance_pct=tolerance_pct)
    status["as_of"] = row["event_date"]
    return status

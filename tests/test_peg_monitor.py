"""
SAR/USD peg monitor (S9 — harvested from Alaa's parallel build).
"""
from datetime import datetime, timezone

from db.sqlite import connection
from trader.regime.peg import peg_status, latest_peg_status, PEG_RATE


def test_peg_intact_within_band():
    s = peg_status(3.7505)
    assert s["known"] and s["intact"] is True
    assert abs(s["deviation_pct"]) <= 0.5
    assert "no FX risk" in s["note"]


def test_peg_drift_flagged_outside_band():
    s = peg_status(3.90)             # ~+4% off the 3.75 peg
    assert s["known"] and s["intact"] is False
    assert s["deviation_pct"] > 0.5
    assert "⚠" in s["note"]


def test_peg_unknown_when_no_rate():
    s = peg_status(None)
    assert s["known"] is False and s["intact"] is None


def test_latest_peg_status_none_when_no_series(dbs):
    assert latest_peg_status(dbs) is None       # dormant-safe: no USDSAR ingested


def test_latest_peg_status_reads_observation(dbs):
    now = datetime.now(timezone.utc).isoformat()
    with connection(dbs.macro) as conn:
        conn.execute(
            "INSERT INTO macro_observations (series_id, indicator, region, value, event_date, "
            "reported_at, ingested_at, known_at, source_id) VALUES (?,?,?,?,?,?,?,?,?)",
            ("USDSAR", "fx_rate", "SA", 3.7502, "2026-06-06", now, now, now, "test"),
        )
    s = latest_peg_status(dbs)
    assert s is not None and s["intact"] is True
    assert s["peg"] == PEG_RATE and s["as_of"] == "2026-06-06"

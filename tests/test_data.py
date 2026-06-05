"""
Sprint 2 — Data ingestion + triangulation tests.

Gate: prices land in the DB; multi-source disagreement flag fires on injected bad data.
Alpaca API is NOT called in these tests — we test the storage + triangulation layer.
"""
import pytest
from db.sqlite import init_db
from data.store import store_price, get_prices
from data.triangulation import (
    check_disagreement, get_consensus_price, DISAGREEMENT_THRESHOLD,
)


@pytest.fixture
def tmp_db(tmp_path):
    db = str(tmp_path / "adam.db")
    init_db(db)
    return db


# ─────────────────────── price storage ──────────────────────────

def test_store_and_retrieve_price(tmp_db):
    rec = dict(symbol="SPUS", date="2026-06-04",
               open=50.0, high=51.0, low=49.5, close=50.5,
               volume=100_000, adj_close=50.5)
    store_price(tmp_db, rec, source="alpaca")
    rows = get_prices(tmp_db, "SPUS", "2026-06-04")
    assert len(rows) == 1
    assert rows[0]["close"] == pytest.approx(50.5)
    assert rows[0]["source"] == "alpaca"

def test_store_upsert_same_source(tmp_db):
    rec = dict(symbol="SPUS", date="2026-06-04",
               open=50.0, high=51.0, low=49.5, close=50.5,
               volume=100_000, adj_close=50.5)
    store_price(tmp_db, rec, source="alpaca")
    rec["close"] = 50.8
    store_price(tmp_db, rec, source="alpaca")
    rows = get_prices(tmp_db, "SPUS", "2026-06-04")
    assert len(rows) == 1       # upserted, not duplicated
    assert rows[0]["close"] == pytest.approx(50.8)

def test_multiple_sources_stored_separately(tmp_db):
    rec = dict(symbol="HLAL", date="2026-06-04",
               open=30.0, high=30.5, low=29.8, close=30.2,
               volume=50_000, adj_close=30.2)
    store_price(tmp_db, rec, source="alpaca")
    rec["close"] = 30.25
    store_price(tmp_db, rec, source="yfinance")
    rows = get_prices(tmp_db, "HLAL", "2026-06-04")
    assert len(rows) == 2

def test_get_prices_empty_when_no_data(tmp_db):
    rows = get_prices(tmp_db, "MISSING", "2026-06-04")
    assert rows == []


# ─────────────────────── triangulation ──────────────────────────

def test_no_disagreement_single_source(tmp_db):
    rec = dict(symbol="SPUS", date="2026-06-01",
               open=50.0, high=51.0, low=49.5, close=50.5,
               volume=100_000, adj_close=50.5)
    store_price(tmp_db, rec, source="alpaca")
    assert check_disagreement(tmp_db, "SPUS", "2026-06-01") == []

def test_no_disagreement_sources_agree(tmp_db):
    rec = dict(symbol="SPUS", date="2026-06-02",
               open=50.0, high=51.0, low=49.5, close=50.5,
               volume=100_000, adj_close=50.5)
    store_price(tmp_db, rec, source="alpaca")
    store_price(tmp_db, rec, source="yfinance")   # same close
    assert check_disagreement(tmp_db, "SPUS", "2026-06-02") == []

def test_disagreement_flag_fires_on_bad_data(tmp_db):
    """1% close difference triggers the flag — Sprint 2 gate."""
    rec = dict(symbol="SPUS", date="2026-06-03",
               open=50.0, high=51.0, low=49.5, close=50.0,
               volume=100_000, adj_close=50.0)
    store_price(tmp_db, rec, source="alpaca")
    rec["close"] = 50.5   # 1 % difference — above 0.5 % threshold
    store_price(tmp_db, rec, source="yfinance")
    flags = check_disagreement(tmp_db, "SPUS", "2026-06-03")
    assert len(flags) == 1
    assert flags[0].diff_pct > DISAGREEMENT_THRESHOLD

def test_disagreement_below_threshold_not_flagged(tmp_db):
    rec = dict(symbol="SPUS", date="2026-06-04",
               open=50.0, high=51.0, low=49.5, close=50.0,
               volume=100_000, adj_close=50.0)
    store_price(tmp_db, rec, source="alpaca")
    rec["close"] = 50.02  # 0.04 % — below 0.5 % threshold
    store_price(tmp_db, rec, source="yfinance")
    assert check_disagreement(tmp_db, "SPUS", "2026-06-04") == []

def test_consensus_price_is_median(tmp_db):
    base = dict(symbol="HLAL", date="2026-06-05",
                open=30.0, high=30.5, low=29.8, adj_close=30.0, volume=50_000)
    for close, src in [(30.0, "alpaca"), (31.0, "yfinance"), (30.5, "manual")]:
        store_price(tmp_db, {**base, "close": close}, source=src)
    price, _ = get_consensus_price(tmp_db, "HLAL", "2026-06-05")
    assert price == pytest.approx(30.5)   # median of [30.0, 30.5, 31.0]

def test_consensus_no_data_returns_none(tmp_db):
    price, flags = get_consensus_price(tmp_db, "GHOST", "2026-06-05")
    assert price is None
    assert flags == []

def test_consensus_returns_disagreements(tmp_db):
    rec = dict(symbol="MNZL", date="2026-06-06",
               open=60.0, high=61.0, low=59.5, adj_close=60.0, volume=20_000)
    store_price(tmp_db, {**rec, "close": 60.0}, source="alpaca")
    store_price(tmp_db, {**rec, "close": 61.0}, source="yfinance")  # ~1.65%
    price, flags = get_consensus_price(tmp_db, "MNZL", "2026-06-06")
    assert price is not None
    assert len(flags) == 1

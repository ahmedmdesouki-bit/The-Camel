"""
S9 slice 2 — Regime Engine: feature builder (over macro_observations) + classifier + history.
"""
import sqlite3
import pytest

from trader.regime import (
    Regime, classify, regime_to_themes, build_features, record_regime, latest_regime,
)


def _seed(dbs, series_id, value, event_date):
    with sqlite3.connect(dbs.macro) as c:
        c.execute(
            "INSERT INTO macro_observations (series_id, value, event_date, known_at, source_id) "
            "VALUES (?,?,?,?,?)", (series_id, value, event_date, "2026-06-06", "test"))
        c.commit()


# ---------------- classifier (unit; deterministic feature dicts) ----------------

def test_inflation_shock():
    assert classify({"cpi_yoy": 6.0}).regime == Regime.INFLATION_SHOCK

def test_recession_risk_from_curve_and_credit():
    r = classify({"yield_curve": -0.5, "hy_spread": 6.0})
    assert r.regime == Regime.RECESSION_RISK and 0 < r.confidence <= 1

def test_liquidity_expansion():
    assert classify({"fed_funds": 0.25, "cpi_yoy": 2.0}).regime == Regime.LIQUIDITY_EXPANSION

def test_liquidity_tightening():
    assert classify({"fed_funds": 5.0}).regime == Regime.LIQUIDITY_TIGHTENING

def test_commodity_supply_shock():
    assert classify({"oil_change_pct": 30.0}).regime == Regime.COMMODITY_SUPPLY_SHOCK

def test_geopolitical_risk_off_on_high_vix():
    assert classify({"vix": 35.0}).regime == Regime.GEOPOLITICAL_RISK_OFF

def test_usd_strength_regime():
    assert classify({"usd": 125.0}).regime == Regime.USD_STRENGTH_EM_PRESSURE

def test_no_data_is_unknown():
    r = classify({})
    assert r.regime == Regime.UNKNOWN and r.confidence == 0.0

def test_benign_macro_is_recovery():
    assert classify({"fed_funds": 2.5, "cpi_yoy": 3.0}).regime == Regime.RECOVERY


# ---------------- themes ----------------

def test_regime_to_themes():
    assert "energy" in regime_to_themes(Regime.INFLATION_SHOCK)
    assert "defensives" in regime_to_themes(Regime.RECESSION_RISK)
    assert regime_to_themes(Regime.UNKNOWN) == []


# ---------------- feature builder over real macro_observations ----------------

def test_build_features_derives_curve_and_classifies_recession(dbs):
    _seed(dbs, "DGS10", 4.3, "2026-05-01")
    _seed(dbs, "DGS2", 4.8, "2026-05-01")          # inverted curve
    _seed(dbs, "BAMLH0A0HYM2", 6.0, "2026-05-01")  # wide HY
    f = build_features(dbs)
    assert f["yield_curve"] == pytest.approx(-0.5) and f["hy_spread"] == pytest.approx(6.0)
    assert classify(f).regime == Regime.RECESSION_RISK

def test_build_features_computes_cpi_yoy(dbs):
    _seed(dbs, "CPIAUCSL", 300.0, "2025-05-01")
    _seed(dbs, "CPIAUCSL", 318.0, "2026-05-01")    # +6% YoY
    f = build_features(dbs)
    assert f["cpi_yoy"] == pytest.approx(6.0)
    assert classify(f).regime == Regime.INFLATION_SHOCK

def test_build_features_is_point_in_time(dbs):
    _seed(dbs, "VIXCLS", 15.0, "2026-01-01")
    _seed(dbs, "VIXCLS", 35.0, "2026-06-01")
    assert build_features(dbs, as_of="2026-03-01")["vix"] == pytest.approx(15.0)  # earlier only
    assert build_features(dbs)["vix"] == pytest.approx(35.0)                       # latest


# ---------------- history store ----------------

def test_record_and_read_latest_regime(dbs):
    r = classify({"cpi_yoy": 6.0})
    record_regime(dbs, r, now="2026-06-06T00:00:00+00:00")
    latest = latest_regime(dbs)
    assert latest["regime"] == "INFLATION_SHOCK" and latest["features"]["cpi_yoy"] == 6.0

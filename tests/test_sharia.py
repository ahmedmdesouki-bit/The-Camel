"""
Sprint 2 — Sharia gate tests.  DB: dbs.sharia (camel_sharia.db).
"""
import pytest
from sharia.classifier import classify_business_model
from sharia.screener import Financials, screen_instrument, run_quarterly_rescreen
from sharia.whitelist import (
    add_instrument, freeze_instrument, get_instrument, load_whitelist,
)
from guardrail.constitution import (
    Action, ActionType, Constitution, Instrument, PortfolioState, Thesis,
)


@pytest.fixture
def tmp_db(dbs):
    return dbs.sharia


# ─────────────────────────── classifier ─────────────────────────

def test_clean_business_approved():
    r = classify_business_model("An AI-powered halal recipe recommendation app")
    assert r.approved and r.flags == []

def test_gambling_rejected():
    r = classify_business_model("A sports betting platform and casino app")
    assert not r.approved and "gambling" in r.flags

def test_alcohol_rejected():
    r = classify_business_model("An e-commerce site for premium wines and spirits")
    assert not r.approved and "alcohol" in r.flags

def test_tobacco_rejected():
    r = classify_business_model("A subscription delivery for cigarettes and vape pens")
    assert not r.approved and "tobacco" in r.flags

def test_weapons_rejected():
    r = classify_business_model("SaaS for firearm retailers and ammunition tracking")
    assert not r.approved and "weapons" in r.flags

def test_multiple_haram_categories():
    r = classify_business_model("A payday loan and casino app with adult content")
    assert not r.approved and len(r.flags) >= 2

def test_conventional_finance_rejected():
    r = classify_business_model("A mortgage lending platform connecting banks to customers")
    assert not r.approved and "conventional_finance" in r.flags

def test_ai_saas_approved():
    assert classify_business_model("AI productivity tool for legal document summarisation").approved


# ─────────────────── AAOIFI ratio screener ──────────────────────

def test_clean_instrument_passes():
    f = Financials("SPUS", 1_000_000, 100_000, 100_000, 0.01)
    r = screen_instrument(f)
    assert r.passed and r.reasons == []

def test_debt_ratio_breach_fails():
    r = screen_instrument(Financials("X", 1_000_000, 350_000, 50_000, 0.01))
    assert not r.passed and any("debt_ratio" in s for s in r.reasons)

def test_interest_assets_breach_fails():
    # migrated to the verified AAOIFI screen → the liquid-assets ratio (was "interest_assets_ratio")
    r = screen_instrument(Financials("X", 1_000_000, 50_000, 400_000, 0.01))
    assert not r.passed and any("liquid_assets_ratio" in s for s in r.reasons)

def test_haram_income_breach_fails():
    r = screen_instrument(Financials("X", 1_000_000, 50_000, 50_000, 0.06))
    assert not r.passed and any("haram_income_pct" in s for s in r.reasons)

def test_boundary_at_limit_fails():
    # verified AAOIFI limit is 30% (not the old 33%): 31% debt → hard fail
    assert not screen_instrument(Financials("X", 1_000_000, 310_000, 0, 0.0)).passed

def test_boundary_just_under_passes():
    # 25% debt → clean pass, no notes
    r = screen_instrument(Financials("X", 1_000_000, 250_000, 0, 0.0))
    assert r.passed and r.reasons == []

def test_doubtful_band_passes_with_note():
    # 29% debt sits in AAOIFI's doubtful watch band: passes, but carries a near-miss note (not frozen)
    r = screen_instrument(Financials("X", 1_000_000, 290_000, 0, 0.0))
    assert r.passed and any("debt_ratio" in s for s in r.reasons)


# ─────────────────────── whitelist DB ───────────────────────────

def test_add_and_load_instrument(tmp_db):
    add_instrument(tmp_db, "SPUS", "etf", approved_by="chiko", scan_id="scan_001")
    wl = load_whitelist(tmp_db)
    assert "SPUS" in wl
    assert wl["SPUS"].on_whitelist
    assert wl["SPUS"].sharia_status == "compliant"
    assert not wl["SPUS"].frozen

def test_freeze_instrument(tmp_db):
    add_instrument(tmp_db, "HLAL", "etf", approved_by="chiko", scan_id="scan_002")
    freeze_instrument(tmp_db, "HLAL", reason="debt_ratio breach")
    assert get_instrument(tmp_db, "HLAL")["frozen"] == 1

def test_freeze_returns_false_for_unknown(tmp_db):
    assert not freeze_instrument(tmp_db, "GHOST", reason="test")

def test_get_instrument_none_when_absent(tmp_db):
    assert get_instrument(tmp_db, "MISSING") is None


# ─────────────── Constitution integration (Sprint 2 gate) ───────

def test_off_whitelist_rejected_by_constitution(tmp_db):
    wl = load_whitelist(tmp_db)
    state = PortfolioState(fund_usd=10000, cash_usd=5000, whitelist=wl)
    a = Action(type=ActionType.TRADE, symbol="AAPL", side="buy", notional_usd=500,
               instrument_type="equity",
               thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"),
               mode="paper")
    d = Constitution().evaluate(a, state)
    assert not d.allow and d.limit_hit == "off_whitelist"

def test_haram_business_rejected_by_constitution():
    state = PortfolioState(fund_usd=10000, cash_usd=5000)
    a = Action(type=ActionType.DEPLOY, business_model="online sports betting casino")
    d = Constitution().evaluate(a, state)
    assert not d.allow and d.limit_hit == "haram_business"


# ─────────────────── quarterly re-screen ────────────────────────

def test_quarterly_rescreen_freezes_drifted(tmp_db):
    add_instrument(tmp_db, "DRIFTED", "etf", approved_by="chiko", scan_id="s1")
    results = run_quarterly_rescreen(
        tmp_db,
        lambda s: Financials(s, 1_000_000, 400_000, 0, 0.0),
    )
    assert len(results) == 1 and not results[0].passed
    assert get_instrument(tmp_db, "DRIFTED")["frozen"] == 1

def test_quarterly_rescreen_passes_clean(tmp_db):
    add_instrument(tmp_db, "SPUS", "etf", approved_by="chiko", scan_id="s2")
    results = run_quarterly_rescreen(
        tmp_db,
        lambda s: Financials(s, 1_000_000, 100_000, 100_000, 0.01),
    )
    assert results[0].passed and get_instrument(tmp_db, "SPUS")["frozen"] == 0

def test_quarterly_rescreen_skips_frozen(tmp_db):
    add_instrument(tmp_db, "FROZEN", "etf", approved_by="chiko", scan_id="s3")
    freeze_instrument(tmp_db, "FROZEN", reason="pre-frozen")
    calls = []
    run_quarterly_rescreen(
        tmp_db,
        lambda s: calls.append(s) or Financials(s, 1_000_000, 0, 0, 0.0),
    )
    assert "FROZEN" not in calls

"""
Sprint 2 — Sharia gate tests.

Gate: off-whitelist ticker rejected; haram business idea rejected;
re-screen freezes drifted names; clean instruments pass.
"""
import pytest
from db.sqlite import init_db
from sharia.classifier import classify_business_model
from sharia.screener import Financials, screen_instrument, run_quarterly_rescreen
from sharia.whitelist import (
    add_instrument, freeze_instrument, get_instrument, load_whitelist,
)
from guardrail.constitution import (
    Action, ActionType, Constitution, Instrument, PortfolioState, Thesis,
)


# ─────────────────────────── fixtures ───────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    db = str(tmp_path / "adam.db")
    init_db(db)
    return db


# ─────────────────────────── classifier ─────────────────────────

def test_clean_business_approved():
    r = classify_business_model("An AI-powered halal recipe recommendation app")
    assert r.approved
    assert r.flags == []

def test_gambling_rejected():
    r = classify_business_model("A sports betting platform and casino app")
    assert not r.approved
    assert "gambling" in r.flags

def test_alcohol_rejected():
    r = classify_business_model("An e-commerce site for premium wines and spirits")
    assert not r.approved
    assert "alcohol" in r.flags

def test_tobacco_rejected():
    r = classify_business_model("A subscription delivery service for cigarettes and vape pens")
    assert not r.approved
    assert "tobacco" in r.flags

def test_weapons_rejected():
    r = classify_business_model("SaaS platform for firearm retailers and ammunition tracking")
    assert not r.approved
    assert "weapons" in r.flags

def test_multiple_haram_categories():
    r = classify_business_model("A payday loan and casino app with adult content")
    assert not r.approved
    assert len(r.flags) >= 2

def test_conventional_finance_rejected():
    r = classify_business_model("A mortgage lending platform connecting banks to customers")
    assert not r.approved
    assert "conventional_finance" in r.flags

def test_ai_saas_approved():
    r = classify_business_model("AI productivity tool for legal document summarisation")
    assert r.approved


# ─────────────────── AAOIFI ratio screener ──────────────────────

def test_clean_instrument_passes():
    f = Financials("SPUS", market_cap=1_000_000,
                   total_debt=100_000, cash_and_interest_securities=100_000,
                   non_compliant_income_pct=0.01)
    r = screen_instrument(f)
    assert r.passed
    assert r.reasons == []

def test_debt_ratio_breach_fails():
    f = Financials("X", market_cap=1_000_000,
                   total_debt=350_000, cash_and_interest_securities=50_000,
                   non_compliant_income_pct=0.01)
    r = screen_instrument(f)
    assert not r.passed
    assert any("debt_ratio" in reason for reason in r.reasons)

def test_interest_assets_breach_fails():
    f = Financials("X", market_cap=1_000_000,
                   total_debt=50_000, cash_and_interest_securities=400_000,
                   non_compliant_income_pct=0.01)
    r = screen_instrument(f)
    assert not r.passed
    assert any("interest_assets_ratio" in reason for reason in r.reasons)

def test_haram_income_breach_fails():
    f = Financials("X", market_cap=1_000_000,
                   total_debt=50_000, cash_and_interest_securities=50_000,
                   non_compliant_income_pct=0.06)
    r = screen_instrument(f)
    assert not r.passed
    assert any("haram_income_pct" in reason for reason in r.reasons)

def test_boundary_at_limit_fails():
    # exactly 33% debt ratio should fail (≥ threshold)
    f = Financials("X", market_cap=1_000_000,
                   total_debt=330_000, cash_and_interest_securities=0,
                   non_compliant_income_pct=0.0)
    r = screen_instrument(f)
    assert not r.passed

def test_boundary_just_under_passes():
    f = Financials("X", market_cap=1_000_000,
                   total_debt=329_000, cash_and_interest_securities=0,
                   non_compliant_income_pct=0.0)
    r = screen_instrument(f)
    assert r.passed


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
    row = get_instrument(tmp_db, "HLAL")
    assert row["frozen"] == 1

def test_freeze_returns_false_for_unknown(tmp_db):
    assert not freeze_instrument(tmp_db, "GHOST", reason="test")

def test_get_instrument_none_when_absent(tmp_db):
    assert get_instrument(tmp_db, "MISSING") is None


# ─────────────── Constitution integration (Sprint 2 gate) ───────

def test_off_whitelist_rejected_by_constitution(tmp_db):
    """Off-whitelist ticker MUST be rejected — Sprint 2 gate."""
    wl = load_whitelist(tmp_db)   # empty DB → empty whitelist
    state = PortfolioState(fund_usd=10000, cash_usd=5000, whitelist=wl)
    a = Action(
        type=ActionType.TRADE, symbol="AAPL", side="buy", notional_usd=500,
        instrument_type="equity",
        thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"),
        mode="paper",
    )
    d = Constitution().evaluate(a, state)
    assert not d.allow
    assert d.limit_hit == "off_whitelist"

def test_haram_business_rejected_by_constitution():
    """Haram business model MUST be rejected — Sprint 2 gate."""
    state = PortfolioState(fund_usd=10000, cash_usd=5000)
    a = Action(type=ActionType.DEPLOY, business_model="online sports betting casino platform")
    d = Constitution().evaluate(a, state)
    assert not d.allow
    assert d.limit_hit == "haram_business"


# ─────────────────── quarterly re-screen ────────────────────────

def test_quarterly_rescreen_freezes_drifted(tmp_db):
    add_instrument(tmp_db, "DRIFTED", "etf", approved_by="chiko", scan_id="scan_003")

    def get_financials(symbol):
        return Financials(symbol, market_cap=1_000_000,
                          total_debt=400_000, cash_and_interest_securities=0,
                          non_compliant_income_pct=0.0)

    results = run_quarterly_rescreen(tmp_db, get_financials)
    assert len(results) == 1
    assert not results[0].passed
    row = get_instrument(tmp_db, "DRIFTED")
    assert row["frozen"] == 1

def test_quarterly_rescreen_passes_clean(tmp_db):
    add_instrument(tmp_db, "SPUS", "etf", approved_by="chiko", scan_id="scan_004")

    def get_financials(symbol):
        return Financials(symbol, market_cap=1_000_000,
                          total_debt=100_000, cash_and_interest_securities=100_000,
                          non_compliant_income_pct=0.01)

    results = run_quarterly_rescreen(tmp_db, get_financials)
    assert len(results) == 1
    assert results[0].passed
    row = get_instrument(tmp_db, "SPUS")
    assert row["frozen"] == 0

def test_quarterly_rescreen_skips_frozen(tmp_db):
    add_instrument(tmp_db, "FROZEN", "etf", approved_by="chiko", scan_id="scan_005")
    freeze_instrument(tmp_db, "FROZEN", reason="pre-frozen")

    calls = []

    def get_financials(symbol):
        calls.append(symbol)
        return Financials(symbol, market_cap=1_000_000,
                          total_debt=0, cash_and_interest_securities=0,
                          non_compliant_income_pct=0.0)

    run_quarterly_rescreen(tmp_db, get_financials)
    assert "FROZEN" not in calls

"""
Sprint 3 — Thesis / base-rate engine tests.
"""
import pytest
from trader.engine.thesis import BaseRateCard, ThesisCard
from guardrail.constitution import Thesis


# ─────────────────── ThesisCard ─────────────────────────────────

def test_complete_thesis_passes():
    tc = ThesisCard(
        symbol="SPUS", thesis="ETF rotation thesis",
        invalidation="close < 50d MA",
        profit_take="+15%", time_stop="6 months",
    )
    assert tc.is_complete()

def test_incomplete_thesis_missing_invalidation():
    tc = ThesisCard(symbol="SPUS", profit_take="+10%", time_stop="3 months")
    assert not tc.is_complete()

def test_incomplete_thesis_missing_profit_take():
    tc = ThesisCard(symbol="SPUS", invalidation="close < 50d MA", time_stop="3 months")
    assert not tc.is_complete()

def test_incomplete_thesis_missing_time_stop():
    tc = ThesisCard(symbol="SPUS", invalidation="x", profit_take="y")
    assert not tc.is_complete()

def test_whitespace_only_fields_count_as_missing():
    tc = ThesisCard(symbol="SPUS", invalidation="  ", profit_take="y", time_stop="z")
    assert not tc.is_complete()

def test_to_guardrail_thesis_maps_fields():
    tc = ThesisCard(
        symbol="SPUS",
        invalidation="close < 50d MA",
        profit_take="+15%",
        time_stop="6 months",
    )
    t: Thesis = tc.to_guardrail_thesis()
    assert t.invalidation == "close < 50d MA"
    assert t.profit_take == "+15%"
    assert t.time_stop == "6 months"
    assert t.complete()

def test_warnings_no_thesis_text():
    tc = ThesisCard(symbol="SPUS", invalidation="x", profit_take="y", time_stop="z")
    warnings = tc.warnings()
    assert any("thesis" in w for w in warnings)

def test_warnings_no_base_rate():
    tc = ThesisCard(symbol="SPUS", thesis="ok", invalidation="x",
                    profit_take="y", time_stop="z")
    assert any("base-rate" in w for w in tc.warnings())

def test_warnings_clean_thesis():
    br = BaseRateCard(signal="RSI bounce", comparables_n=30, horizon="3m",
                      hit_rate=0.6, median_magnitude="+8%",
                      already_priced_in="some", overfitting_check="ok",
                      probability_tilt="lean long")
    tc = ThesisCard(symbol="SPUS", thesis="Strong thesis", invalidation="x",
                    profit_take="y", time_stop="z", base_rate=br,
                    opportunity_cost_justification="higher risk-adjusted return than SPUS beta")
    assert tc.warnings() == []


# ---------------- S4: opportunity-cost gate + trade-ready ----------------

def test_warnings_flags_missing_opportunity_cost():
    tc = ThesisCard(symbol="SPUS", thesis="ok", invalidation="x",
                    profit_take="y", time_stop="z")
    assert any("opportunity-cost" in w for w in tc.warnings())

def test_is_trade_ready_requires_opportunity_cost():
    tc = ThesisCard(symbol="SPUS", invalidation="x", profit_take="y", time_stop="z")
    assert tc.is_complete()            # Constitution minimum met
    assert not tc.is_trade_ready()     # but not trade-ready without the justification
    tc.opportunity_cost_justification = "asymmetric setup vs index beta"
    assert tc.is_trade_ready()

def test_is_trade_ready_needs_complete_invalidation():
    tc = ThesisCard(symbol="SPUS", profit_take="y", time_stop="z",
                    opportunity_cost_justification="x")
    assert not tc.is_trade_ready()     # missing price invalidation


# ─────────────────── BaseRateCard ───────────────────────────────

def test_low_trust_below_10():
    br = BaseRateCard(comparables_n=5)
    assert br.low_trust()

def test_low_trust_exactly_10():
    br = BaseRateCard(comparables_n=10)
    assert not br.low_trust()

def test_high_trust():
    br = BaseRateCard(comparables_n=50)
    assert not br.low_trust()

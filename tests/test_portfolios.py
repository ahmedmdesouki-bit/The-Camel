"""
S11b — Portfolio Engine: the 6 seed portfolios, allocation, lifecycle, tolerance-band rebalancing
(suggestions only), 4-level risk budgets, and persistence round-trip.
"""
from portfolios.engine import (
    PortfolioManager, PortfolioPhase, SEED_PORTFOLIOS,
    advance_phase, allocate, tolerance_band_rebalance, check_risk_budget,
)


def test_seed_weights_sum_to_one():
    m = PortfolioManager(SEED_PORTFOLIOS)
    assert m.total_weight() == 1.0 and len(m.all()) == 6


def test_allocation_by_target_weight():
    alloc = allocate(SEED_PORTFOLIOS, 10_000)
    assert alloc["core_sharia_growth"] == 4000.0 and alloc["cash_waiting_room"] == 1500.0


def test_strategies_assigned_per_portfolio():
    m = PortfolioManager(SEED_PORTFOLIOS)
    assert m.strategies_for("core_sharia_growth") == ["core_dca", "etf_regime_rotation"]
    assert m.strategies_for("income_dividend") == ["dividend_growth"]
    assert m.strategies_for("cash_waiting_room") == []


def test_lifecycle_advances_one_rung_and_stops_at_scale():
    assert advance_phase(PortfolioPhase.INCUBATE) == PortfolioPhase.QUALIFY
    assert advance_phase(PortfolioPhase.PILOT) == PortfolioPhase.SCALE
    assert advance_phase(PortfolioPhase.SCALE) == PortfolioPhase.SCALE   # caps at scale


def test_tolerance_band_emits_suggestions_only():
    current = {"a": 0.50, "b": 0.10}
    target = {"a": 0.40, "b": 0.10}
    sugg = tolerance_band_rebalance(current, target, band=0.05)
    assert len(sugg) == 1 and sugg[0].portfolio_id == "a" and sugg[0].action == "reduce"
    # within band → nothing
    assert tolerance_band_rebalance({"a": 0.42}, {"a": 0.40}, band=0.05) == []


def test_risk_budget_breaches():
    p = SEED_PORTFOLIOS[2]   # thematic_satellite, max_drawdown 30%, gross limit 100%
    assert check_risk_budget(p, gross_exposure_pct=0.5, drawdown_pct=-0.1) == []
    over = check_risk_budget(p, gross_exposure_pct=1.2, drawdown_pct=-0.4, max_sector_pct=0.6)
    assert len(over) == 3   # gross, drawdown, and sector cap all breached


def test_cash_room_holds_no_exposure():
    p = next(p for p in SEED_PORTFOLIOS if p.portfolio_id == "cash_waiting_room")
    assert p.gross_exposure_limit_pct == 0.0 and p.cash_min_pct == 1.0
    assert check_risk_budget(p, gross_exposure_pct=0.1)   # any exposure breaches


def test_multi_benchmark():
    p = SEED_PORTFOLIOS[0]
    b = p.benchmarks()
    assert b["policy"] == "SPUS" and "opportunity" in b and b["cash"] == "CASH"


def test_persistence_round_trip(dbs):
    PortfolioManager.seed(dbs)                    # writes the 6 seeds
    loaded = PortfolioManager.load(dbs)
    assert {p.portfolio_id for p in loaded.all()} == {p.portfolio_id for p in SEED_PORTFOLIOS}
    assert loaded.get("income_dividend").assigned_strategies == ["dividend_growth"]
    assert loaded.total_weight() == 1.0

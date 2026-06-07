"""
S11.5 — system integration: the keystone that connects S9–S11 at runtime.

Proves the driver runs REAL strategy signals through the FULL Edge Proof and the assembled loop
(not v0, not caller-injected reports), and that per-portfolio holdings reconcile to the fund.
"""
from datetime import date, timedelta

from db.sqlite import connection
from data.store import store_price
from guardrail.constitution import PortfolioState, Instrument
from trader.strategies.registry import StrategyRegistry
from trader.strategies.quality_momentum import QualityMomentum
from loop.driver import run_strategy_tick, build_context
from trader.portfolios.holdings import apply_portfolio_fill, holdings, reconcile_to_fund, fund_rollup


def _seed(dbs, symbol, closes, start="2023-01-01"):
    d0 = date.fromisoformat(start)
    for k, c in enumerate(closes):
        store_price(dbs.market, {"symbol": symbol, "date": (d0 + timedelta(days=k)).isoformat(),
                                 "close": c, "adj_close": c}, source="test")


def _state():
    wl = {"AAPL": Instrument("AAPL", sector="tech", sharia_status="compliant",
                             frozen=False, on_whitelist=True)}
    return PortfolioState(fund_usd=1000, cash_usd=1000, whitelist=wl)


# ---------------- the integration driver ----------------

def test_driver_runs_strategy_signal_through_full_edge_and_loop(dbs):
    # AAPL trends up strongly (momentum signal + beats the flat benchmark in the full Edge Proof)
    _seed(dbs, "AAPL", [100.0 + k for k in range(320)])
    _seed(dbs, "SPUS", [200.0] * 320)
    with connection(dbs.sharia) as conn:
        conn.execute("INSERT INTO sharia_status (symbol, final_status) VALUES ('AAPL','pass')")

    reg = StrategyRegistry()
    reg.register(QualityMomentum())

    ctx = build_context(dbs, ["AAPL"], cash_usd=1000)
    assert ctx.regime is not None and ctx.whitelist["AAPL"] == "pass"   # context built from governed DBs

    result = run_strategy_tick(dbs, reg, _state(), symbols=["AAPL"], budget_usd=500.0)
    assert result.router_path == "trader"          # a real proven edge moved the router off Wait
    assert "AAPL" in result.executed               # strategy → full Edge Proof → loop → executed


def test_driver_blocks_when_no_real_edge(dbs):
    # AAPL trends up (so the strategy proposes it) but the benchmark trends up FASTER → no excess edge
    _seed(dbs, "AAPL", [100.0 + k for k in range(320)])
    _seed(dbs, "SPUS", [100.0 + 3 * k for k in range(320)])
    with connection(dbs.sharia) as conn:
        conn.execute("INSERT INTO sharia_status (symbol, final_status) VALUES ('AAPL','pass')")
    reg = StrategyRegistry(); reg.register(QualityMomentum())

    result = run_strategy_tick(dbs, reg, _state(), symbols=["AAPL"], budget_usd=500.0)
    assert result.executed == []                   # proposed, but the full Edge Proof rejected it → no trade


# ---------------- per-portfolio accounting (A2) ----------------

def test_portfolio_holdings_weighted_avg_and_phantom_guard(dbs):
    apply_portfolio_fill(dbs, "core_sharia_growth", "SPUS", "buy", 2, 100.0)
    apply_portfolio_fill(dbs, "core_sharia_growth", "SPUS", "buy", 2, 110.0)
    h = holdings(dbs, "core_sharia_growth")[0]
    assert h["qty"] == 4 and h["avg_cost"] == 105.0          # weighted average

    import pytest
    with pytest.raises(ValueError):
        apply_portfolio_fill(dbs, "core_sharia_growth", "SPUS", "sell", 10, 100.0)   # phantom guard


def test_portfolios_reconcile_to_fund(dbs):
    apply_portfolio_fill(dbs, "core_sharia_growth", "SPUS", "buy", 3, 100.0)
    apply_portfolio_fill(dbs, "income_dividend", "SPUS", "buy", 2, 100.0)
    assert fund_rollup(dbs) == {"SPUS": 5.0}
    assert reconcile_to_fund(dbs, {"SPUS": 5.0}) == []        # per-portfolio sums to the fund
    mismatch = reconcile_to_fund(dbs, {"SPUS": 4.0})          # fund book disagrees
    assert mismatch and mismatch[0]["diff"] == 1.0

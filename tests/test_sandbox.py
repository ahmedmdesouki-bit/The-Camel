"""
S12c — Sandbox Mode: the full assembled system on a (stub) live feed with virtual money via the
realistic-paper executor. Proves a real strategy candidate flows through the WHOLE stack (regime →
strategy → full Edge Proof → Constitution → realistic fill) and that the No-Edge protocol fires when
nothing trades. No network — the quote feed is injected.
"""
from datetime import date, timedelta

from db.sqlite import connection
from data.store import store_price
from guardrail.constitution import PortfolioState, Instrument
from strategies.registry import StrategyRegistry
from strategies.quality_momentum import QualityMomentum
from execution.models import MarketSnapshot, FillStatus
from sandbox.runner import SandboxRunner


def _seed(dbs, symbol, closes, start="2023-01-01"):
    d0 = date.fromisoformat(start)
    for k, c in enumerate(closes):
        store_price(dbs.market, {"symbol": symbol, "date": (d0 + timedelta(days=k)).isoformat(),
                                 "close": c, "adj_close": c}, source="test")


def _state():
    wl = {"AAPL": Instrument("AAPL", sector="tech", sharia_status="compliant", frozen=False, on_whitelist=True)}
    return PortfolioState(fund_usd=10000, cash_usd=10000, whitelist=wl)


def _feed(_sym):
    return MarketSnapshot(symbol="AAPL", bid=71.5, ask=72.0, last=71.8, displayed_size=100,
                          as_of="2026-06-07T15:00:00+00:00")


def test_sandbox_runs_full_stack_to_a_virtual_fill(dbs):
    _seed(dbs, "AAPL", [40.0 + 0.1 * k for k in range(320)])    # uptrend → momentum + beats benchmark
    _seed(dbs, "SPUS", [50.0] * 320)
    with connection(dbs.sharia) as conn:
        conn.execute("INSERT INTO sharia_status (symbol, final_status) VALUES ('AAPL','pass')")
    reg = StrategyRegistry(); reg.register(QualityMomentum())

    out = SandboxRunner(dbs, reg, feed=_feed).run_tick(["AAPL"], _state(), notional_per_trade=500.0)
    assert out.tick.router_path == "trader"              # a proven edge moved the router off Wait
    assert "AAPL" in out.filled                          # full stack → realistic-paper FILLED
    fill = out.fills[0]
    assert fill.status == FillStatus.FILLED and fill.fill_price == 72.0 and fill.filled_qty == 6  # int(500/72)
    assert fill.fees > 0                                  # realistic paper charges fees


def test_sandbox_no_edge_falls_back_to_dca(dbs):
    _seed(dbs, "AAPL", [50.0] * 320)                      # flat → no momentum signal → no candidate
    _seed(dbs, "SPUS", [50.0] * 320)
    reg = StrategyRegistry(); reg.register(QualityMomentum())

    out = SandboxRunner(dbs, reg, feed=_feed).run_tick(["AAPL"], _state())
    assert out.filled == [] and out.no_edge == "core_dca"   # nothing traded → DCA, never idle on capital


def test_sandbox_rejects_stale_quote(dbs):
    _seed(dbs, "AAPL", [40.0 + 0.1 * k for k in range(320)])
    _seed(dbs, "SPUS", [50.0] * 320)
    with connection(dbs.sharia) as conn:
        conn.execute("INSERT INTO sharia_status (symbol, final_status) VALUES ('AAPL','pass')")
    reg = StrategyRegistry(); reg.register(QualityMomentum())

    def stale_feed(_sym):
        return MarketSnapshot(symbol="AAPL", bid=71.5, ask=72.0, displayed_size=100,
                              as_of="2026-06-07T15:00:00+00:00")
    # 'now' is an hour after the quote → the realistic executor must reject it
    out = SandboxRunner(dbs, reg, feed=stale_feed, now="2026-06-07T16:00:00+00:00").run_tick(
        ["AAPL"], _state(), notional_per_trade=500.0)
    assert out.filled == [] and out.fills[0].status == FillStatus.REJECTED and "stale" in out.fills[0].reason

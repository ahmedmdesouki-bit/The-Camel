"""
S10.5 — the assembled operator loop (the Phase-1 blocker) + the scheduled-ops entrypoints.

The load-bearing invariant: **a buy with no passing EdgeReport is rejected by the ASSEMBLED loop**,
because every action is routed through the Allocator (Edge Proof + Constitution), not the Constitution
directly. Also covers router-leans-to-wait, the Budget Kernel in the act path, the phase-gated human
approval gate, the kill switch, and the daily/weekly job entrypoints.
"""
from guardrail.constitution import Action, ActionType, PortfolioState, Instrument, Thesis
from capital.budget_kernel import BudgetKernel, BudgetLimits
from trader.engine.edge_proof import run_full_edge_proof
from loop.assembled import AssembledLoop
from loop.jobs import run_daily_ops, run_weekly_safety
from ops.kill_switch import halt
from alerts.telegram import TelegramNotifier


def _state():
    wl = {s: Instrument(symbol=s, sector="tech", sharia_status="compliant", frozen=False,
                        on_whitelist=True) for s in ("AAPL", "MSFT")}
    return PortfolioState(fund_usd=1000, cash_usd=1000, whitelist=wl)


def _buy(sym, notional=50.0):
    return Action(ActionType.TRADE, symbol=sym, side="buy", notional_usd=notional,
                  thesis=Thesis("price < 150", "+20%", "90d"), mode="paper")


def _pass_edge(sym):
    return run_full_edge_proof(
        symbol=sym, signal="quality_momentum", signal_definition="12-1 momentum, low debt",
        forward_returns=[0.05] * 60, benchmark_median_return=0.01, benchmark="SPUS",
        regime_filtered_returns=[0.05] * 25, recent_returns=[0.05] * 20, n_signals_tested=1,
        sharia_status="pass", data_quality_score=0.85, source_quorum=2, price=180.0,
        budget_usd=200.0, position_pct=0.05, mode="enforcing")


# ---------------- routing ----------------

def test_no_edge_anywhere_router_waits(dbs):
    r = AssembledLoop(dbs).run_tick([_buy("AAPL")], _state(), edge_reports={})
    assert r.router_path == "wait" and r.executed == []      # cannot pick Trader without a proven edge


# ---------------- THE invariant ----------------

def test_assembled_loop_blocks_buy_without_edge(dbs):
    # AAPL has a passing edge (so the router picks Trader); MSFT has NO edge report.
    r = AssembledLoop(dbs).run_tick([_buy("AAPL"), _buy("MSFT")], _state(),
                                    edge_reports={"AAPL": _pass_edge("AAPL")})
    assert r.router_path == "trader"
    assert "AAPL" in r.executed                               # edge + constitution passed → executed
    msft = next(o for o in r.outcomes if o.symbol == "MSFT")
    assert not msft.approved and msft.stage == "edge_or_constitution"   # no edge → blocked BY THE LOOP


# ---------------- budget + approval + kill switch ----------------

def test_budget_kernel_blocks_in_act_path(dbs):
    bk = BudgetKernel(BudgetLimits(total_fund=1000, max_per_action=10, max_daily_spend=100,
                                   max_weekly_spend=500, max_monthly_spend=1000))
    r = AssembledLoop(dbs, budget_kernel=bk).run_tick(
        [_buy("AAPL", 50)], _state(), edge_reports={"AAPL": _pass_edge("AAPL")})
    o = next(o for o in r.outcomes if o.symbol == "AAPL")
    assert not o.approved and o.stage == "budget"             # passed edge+constitution, over budget


def test_phase1_requires_human_approval(dbs):
    er = {"AAPL": _pass_edge("AAPL")}
    blocked = AssembledLoop(dbs, phase=1).run_tick([_buy("AAPL")], _state(), edge_reports=er)
    o = next(o for o in blocked.outcomes if o.symbol == "AAPL")
    assert not o.approved and o.stage == "approval"           # live phase, default withholds approval
    ok = AssembledLoop(dbs, phase=1, approval_fn=lambda a: True).run_tick(
        [_buy("AAPL")], _state(), edge_reports=er)
    assert "AAPL" in ok.executed


def test_kill_switch_halts_the_tick(dbs):
    halt()
    r = AssembledLoop(dbs).run_tick([_buy("AAPL")], _state(),
                                    edge_reports={"AAPL": _pass_edge("AAPL")})
    assert r.halted and r.executed == []                     # conftest resumes the switch after the test


def test_executed_action_is_logged(dbs):
    AssembledLoop(dbs).run_tick([_buy("AAPL")], _state(), edge_reports={"AAPL": _pass_edge("AAPL")})
    from db.sqlite import connection
    with connection(dbs.portfolio) as conn:
        n = conn.execute("SELECT COUNT(*) FROM op_log WHERE event_type='ACT'").fetchone()[0]
    assert n >= 1


# ---------------- scheduled jobs (Workstream B) ----------------

def test_run_daily_ops_renders_and_briefs(dbs, tmp_path):
    out = str(tmp_path / "dash.html")
    summary = run_daily_ops(dbs, notifier=TelegramNotifier(None, None), dashboard_path=out)
    assert summary["dashboard"] == out
    assert "THE CAMEL" in summary.get("brief_preview", "")
    assert summary["errors"] == {}


def test_run_weekly_safety_runs(dbs, tmp_path):
    res = run_weekly_safety(dbs, str(tmp_path / "backups"))
    assert isinstance(res, dict) and "ok" in res

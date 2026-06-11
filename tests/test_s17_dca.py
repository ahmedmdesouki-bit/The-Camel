"""
S17 — No-Edge → DCA execution path: the designed-but-unwired humble default, now WIRED.

When NO candidate proves an edge but capital is idle, the loop deploys mechanical DCA into the compliant
core — edge-EXEMPT (it is the benchmark, not an alpha bet), exactly the way reduce-only sells are exempt.
The edge-exemption is the ONLY relaxation: Sharia/Constitution/Budget/Approval/kill-switch all still gate
it, and ALPHA buys still require a proven edge. These tests pin all of that, including THE gate — a
production `run_trading_tick` that DCAs into the core via the real PaperBroker and grades the run
'complete', advancing the >=28-run live-readiness clock on a no-edge name.
"""
from datetime import datetime, timedelta, timezone

from db.sqlite import connection
from ledger.writer import append_entry
from data.store import store_price
from broker.paper import PaperBroker
from broker.positions import held_qty
from guardrail.constitution import (Action, ActionType, PortfolioState, Thesis, Decision, Constitution)
from capital.allocator import Allocator
from sharia.whitelist import add_instrument, freeze_instrument, load_whitelist
from loop.assembled import AssembledLoop
from loop.driver import run_strategy_tick
from loop.jobs import run_trading_tick, _build_portfolio_state
from trader.strategies.registry import StrategyRegistry
from trader.strategies.core_dca import CoreDCA


def _con(tmp_path, phase=0):
    return Constitution.from_yaml(_yaml(tmp_path, phase))


def _yaml(tmp_path, phase=0):
    p = tmp_path / "limits.yaml"
    p.write_text(f"phase: {phase}\nmax_position_pct: 0.50\nper_order_envelope_usd: 500\n", encoding="utf-8")
    return str(p)


def _seed(dbs, symbol="SPUS", price=50.0, cash=10000.0):
    """Whitelist a compliant core ETF, seed a price, deposit paper cash."""
    add_instrument(dbs.sharia, symbol, "etf", approved_by="founder", scan_id="t-1")
    store_price(dbs.market, {"symbol": symbol, "date": "2026-01-02", "open": price, "high": price,
                             "low": price, "close": price, "volume": 100000, "adj_close": price})
    append_entry(dbs.portfolio, "DEPOSIT", "", cash)


def _dca_action(symbol="SPUS", notional=50.0):
    return Action(ActionType.TRADE, symbol=symbol, side="buy", notional_usd=notional,
                  thesis=Thesis("removed from compliant core / Sharia drift",
                                "long-term accumulation (no profit target)", "none - perpetual DCA"),
                  mode="paper")


def _exe(broker):
    return lambda a: broker.submit(a, Decision(True, "ok"))


# ================= the safety invariant: edge-exemption is scoped to DCA =================

def test_alpha_buy_still_requires_edge_only_dca_is_exempt(dbs, tmp_path):
    """The load-bearing distinction: the SAME buy is BLOCKED with edge required (the alpha path) and
    ALLOWED edge-exempt (the DCA path). Wiring DCA never opened a hole for un-proven alpha."""
    _seed(dbs)
    state = PortfolioState(fund_usd=10000, cash_usd=10000, positions={}, whitelist=load_whitelist(dbs.sharia))
    alloc = Allocator(_con(tmp_path))
    act = _dca_action()
    blocked = alloc.request(act, state)                              # buy default require_edge -> True
    assert not blocked.approved and "edge" in blocked.decision.reason.lower()
    assert alloc.request(act, state, require_edge=False).approved   # edge-exempt DCA -> allowed


# ================= run_dca direct (governed execution) =================

def test_run_dca_fills_through_real_broker(dbs, tmp_path):
    _seed(dbs)
    broker = PaperBroker(dbs.portfolio, dbs.market)
    loop = AssembledLoop(dbs, allocator=Allocator(_con(tmp_path)), broker_execute=_exe(broker))
    outcomes = loop.run_dca([_dca_action()], _build_portfolio_state(dbs))
    assert outcomes and outcomes[0].stage == "executed"
    assert held_qty(dbs.portfolio, "SPUS") > 0
    with connection(dbs.portfolio) as conn:
        assert conn.execute("SELECT COUNT(*) FROM ledger WHERE type='BUY'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM op_log WHERE event_type='DCA'").fetchone()[0] >= 1


def test_run_dca_blocks_frozen_name_constitution_is_still_the_wall(dbs, tmp_path):
    """Edge-exempt does NOT mean Sharia-exempt: a frozen core is blocked by the Constitution even on the
    DCA path — proven through the real gate, nothing fills."""
    _seed(dbs)
    freeze_instrument(dbs.sharia, "SPUS", "compliance drift (test)")
    broker = PaperBroker(dbs.portfolio, dbs.market)
    loop = AssembledLoop(dbs, allocator=Allocator(_con(tmp_path)), broker_execute=_exe(broker))
    outcomes = loop.run_dca([_dca_action()], _build_portfolio_state(dbs))
    assert outcomes[0].stage == "edge_or_constitution" and not outcomes[0].approved
    assert held_qty(dbs.portfolio, "SPUS") == 0


def test_kill_switch_halts_dca(dbs, tmp_path):
    from ops.kill_switch import halt, resume
    _seed(dbs)
    broker = PaperBroker(dbs.portfolio, dbs.market)
    halt()
    try:
        out = AssembledLoop(dbs, allocator=Allocator(_con(tmp_path)),
                            broker_execute=_exe(broker)).run_dca([_dca_action()], _build_portfolio_state(dbs))
    finally:
        resume()
    assert out == [] and held_qty(dbs.portfolio, "SPUS") == 0          # nothing moved


def test_phase1_dca_withheld_until_human_approves(dbs, tmp_path):
    """Phase >= 1: a DCA buy is real capital — it still needs a human, every time. Default withholds;
    an explicit approval fills."""
    _seed(dbs)
    broker = PaperBroker(dbs.portfolio, dbs.market)
    state = _build_portfolio_state(dbs)
    alloc = Allocator(_con(tmp_path))                                 # caps only; the loop's phase gates the human
    withheld = AssembledLoop(dbs, allocator=alloc, phase=1,
                             broker_execute=_exe(broker)).run_dca([_dca_action()], state)
    assert withheld[0].stage == "approval" and not withheld[0].approved
    assert held_qty(dbs.portfolio, "SPUS") == 0                        # nothing moved without a human
    approved = AssembledLoop(dbs, allocator=alloc, phase=1, broker_execute=_exe(broker),
                             approval_fn=lambda a: True).run_dca([_dca_action()], state)
    assert approved[0].stage == "executed" and held_qty(dbs.portfolio, "SPUS") > 0


# ================= the driver fallback (resolve_no_edge wiring) =================

def test_driver_no_edge_with_capital_dcas(dbs, tmp_path):
    """No proven edge + idle cash -> the driver builds an edge-exempt DCA into exactly the core ETF the
    core_dca strategy named, routes 'dca', and attributes the fill to core_dca for the Measure step."""
    _seed(dbs, symbol="AAPL")
    reg = StrategyRegistry()
    reg.register(CoreDCA(core_etf="AAPL"))
    broker = PaperBroker(dbs.portfolio, dbs.market)
    loop = AssembledLoop(dbs, allocator=Allocator(_con(tmp_path)), broker_execute=_exe(broker))
    res = run_strategy_tick(dbs, reg, _build_portfolio_state(dbs), symbols=["AAPL"], loop=loop)
    assert res.router_path == "dca"
    assert res.executed == ["AAPL"]
    assert res.candidate_meta.get("AAPL", {}).get("dca") is True
    assert held_qty(dbs.portfolio, "AAPL") > 0


def test_driver_no_edge_no_capital_waits(dbs, tmp_path):
    """No edge AND no capital -> wait, never a DCA (resolve_no_edge -> 'wait')."""
    _seed(dbs, symbol="AAPL", cash=0.0)
    reg = StrategyRegistry()
    reg.register(CoreDCA(core_etf="AAPL"))
    broker = PaperBroker(dbs.portfolio, dbs.market)
    state = _build_portfolio_state(dbs)
    assert state.cash_usd == 0
    loop = AssembledLoop(dbs, allocator=Allocator(_con(tmp_path)), broker_execute=_exe(broker))
    res = run_strategy_tick(dbs, reg, state, symbols=["AAPL"], loop=loop)
    assert res.executed == [] and res.router_path != "dca"
    assert held_qty(dbs.portfolio, "AAPL") == 0


# ================= THE GATE: production tick DCAs and grades 'complete' =================

def test_production_tick_no_edge_dcas_and_grades_complete(dbs, tmp_path):
    """ONE scheduled run_trading_tick on a funded book with a compliant core and no proven edge: the
    No-Edge -> DCA fallback fires through the real PaperBroker, the run grades 'complete', and the
    >=28-run live-readiness clock advances. The loop now does REAL work on a no-edge name."""
    _seed(dbs)                                                        # SPUS compliant, priced, $10k cash
    reg = StrategyRegistry()
    reg.register(CoreDCA())                                           # core_etf defaults to SPUS
    out = run_trading_tick(dbs, symbols=["SPUS"], config_path=_yaml(tmp_path), registry=reg)
    assert out["router_path"] == "dca"
    assert out["executed"] == ["SPUS"]
    assert out["outcome"] == "complete"
    assert held_qty(dbs.portfolio, "SPUS") > 0
    from ops.live_readiness import _paper_runs
    assert _paper_runs(dbs) >= 1                                      # the autonomy clock advanced
    with connection(dbs.portfolio) as conn:
        row = conn.execute("SELECT outcome FROM runs WHERE id=?", (out["run_id"],)).fetchone()
    assert row["outcome"] == "complete"


def test_production_tick_unfunded_stays_no_action(dbs, tmp_path):
    """No capital -> no DCA -> 'no_action'. The DCA fallback never inflates the readiness clock on an
    empty book."""
    _seed(dbs, cash=0.0)
    reg = StrategyRegistry()
    reg.register(CoreDCA())
    out = run_trading_tick(dbs, symbols=["SPUS"], config_path=_yaml(tmp_path), registry=reg)
    assert out["executed"] == [] and out["outcome"] == "no_action"
    from ops.live_readiness import _paper_runs
    assert _paper_runs(dbs) == 0


def test_dca_cadence_blocks_second_buy_same_day(dbs, tmp_path):
    """DCA cadence (default 1 day): a second tick the same day does NOT re-DCA the core — at most one
    accumulation per name per day, so a sub-daily loop can't over-trade itself into the ground."""
    _seed(dbs)
    reg = StrategyRegistry()
    reg.register(CoreDCA())
    first = run_trading_tick(dbs, symbols=["SPUS"], config_path=_yaml(tmp_path), registry=reg)
    assert first["executed"] == ["SPUS"] and first["outcome"] == "complete"
    second = run_trading_tick(dbs, symbols=["SPUS"], config_path=_yaml(tmp_path), registry=reg)
    assert second["executed"] == [] and second["outcome"] == "no_action"    # cadence-blocked


# ================= P2-C: data-quality gate (Constitution rule #8) wired into the buy path =================

def test_data_eligible_fresh_unknown_source_passes(dbs):
    """A freshly-stored price (unknown source) is decision-eligible: an unknown source label is not 'stale'
    nor 'single-source' — fail-open, freshness is the dominant gate."""
    from data.quality import data_eligible
    _seed(dbs)                                                         # store_price stamps ingested_at=now
    assert data_eligible(dbs, "SPUS").decision_eligible


def test_data_eligible_no_price_data_fails(dbs):
    """Fail-safe: a name with no price data at all is ineligible to drive a buy."""
    from data.quality import data_eligible
    q = data_eligible(dbs, "NOPE")
    assert not q.decision_eligible


def test_stale_price_drops_name_from_buy_rule8(dbs, tmp_path):
    """Constitution rule #8 WIRED: a STALE core price is decision-ineligible -> dropped from the buy set ->
    no DCA fires even with capital (the dropped name is absent from the strategy whitelist, so its signal is
    filtered). The readiness clock cannot advance on stale data."""
    _seed(dbs)                                                         # SPUS compliant, priced, $10k cash
    stale = (datetime.now(timezone.utc) - timedelta(hours=100)).isoformat()
    with connection(dbs.market) as conn:
        conn.execute("UPDATE prices SET ingested_at=? WHERE symbol='SPUS'", (stale,))
    reg = StrategyRegistry()
    reg.register(CoreDCA())
    out = run_trading_tick(dbs, symbols=["SPUS"], config_path=_yaml(tmp_path), registry=reg)
    assert out["executed"] == [] and out["outcome"] == "no_action"
    from ops.live_readiness import _paper_runs
    assert _paper_runs(dbs) == 0

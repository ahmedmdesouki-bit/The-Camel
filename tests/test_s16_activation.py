"""
S16 — Operational Activation & Loop-Closure.

A1 (durable Act + runs persistence): the production tick fills via a real PaperBroker (orders + ledger +
positions), survives a broker that refuses a fill, and writes a `runs` row so the ≥28-run live-readiness
clock can advance.

A2 (Measure → Learn): executed trades are recorded to the learning ledger, round-tripped trades resolve
into win/loss, per-strategy base-rates update (L1), and systematic underperformance files an L3
PROPOSE-ONLY request — never auto-applied. These prove the loop's previously-open back half is closed.
"""
import json

import pytest

from db.sqlite import connection
from ledger.writer import append_entry
from broker.positions import apply_fill, held_qty
from broker.paper import PaperBroker
from guardrail.constitution import Action, ActionType, PortfolioState, Instrument, Thesis, Decision
from trader.engine.edge_proof import run_full_edge_proof
from loop.assembled import AssembledLoop
from loop.jobs import run_trading_tick, ensure_opening_balance
from learning.measure import record_trade_decision, resolve_and_learn
from operator_os.learning_ledger import get_entry
import learning.improvement_proposer as ip


# ---- shared builders (mirror tests/test_assembled_loop.py) ----

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


def _write_yaml(tmp_path, phase):
    p = tmp_path / "limits.yaml"
    p.write_text(f"phase: {phase}\nmax_position_pct: 0.20\nper_order_envelope_usd: 50\n", encoding="utf-8")
    return str(p)


# ================= A1 — durable Act =================

def test_assembled_act_is_durable_via_paper_broker(dbs):
    """A passing edge → the loop fills through a REAL PaperBroker: orders + ledger + positions written
    (not a 'simulated_fill' string)."""
    broker = PaperBroker(dbs.portfolio, dbs.market, allow_fallback_price=True)  # $1 fill, no price seed
    loop = AssembledLoop(dbs, broker_execute=lambda a: broker.submit(
        a, Decision(allow=True, reason="ok")))
    r = loop.run_tick([_buy("AAPL")], _state(), edge_reports={"AAPL": _pass_edge("AAPL")})

    assert r.router_path == "trader" and "AAPL" in r.executed
    assert held_qty(dbs.portfolio, "AAPL") > 0                       # positions updated
    with connection(dbs.portfolio) as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders WHERE status='filled'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM ledger WHERE type='BUY'").fetchone()[0] == 1


def test_broker_refusal_does_not_crash_or_count_as_executed(dbs):
    """A broker that raises at fill time (e.g. no validated price) must NOT crash the tick or be counted
    as executed — it is recorded as an execute_error."""
    def boom(_a):
        raise RuntimeError("no validated price")
    r = AssembledLoop(dbs, broker_execute=boom).run_tick(
        [_buy("AAPL")], _state(), edge_reports={"AAPL": _pass_edge("AAPL")})
    assert "AAPL" not in r.executed
    o = next(o for o in r.outcomes if o.symbol == "AAPL")
    assert o.stage == "execute_error" and not o.approved


def test_production_tick_persists_a_terminal_runs_row(dbs, tmp_path):
    """The founder-scheduled entrypoint now persists a terminal `runs` row (never left 'running'). A
    funded book with no proven edge waits → a NON-counting 'no_action' outcome, not a fake 'complete'."""
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    out = run_trading_tick(dbs, symbols=[], config_path=_write_yaml(tmp_path, 0))
    assert out["run_id"] is not None and out["outcome"] == "no_action"
    with connection(dbs.portfolio) as conn:
        row = conn.execute("SELECT outcome, ended_at, steps_json FROM runs WHERE id=?",
                           (out["run_id"],)).fetchone()
    assert row["outcome"] == "no_action" and row["ended_at"] is not None    # not stuck 'running'
    # de-vacuumed: assert the actual step statuses, not just substring presence
    steps = {s["name"]: s["status"] for s in json.loads(row["steps_json"])}
    assert steps["measure"] == "ok" and steps["learn"] == "ok"   # Measure→Learn actually ran
    assert steps["act"] == "skipped"                             # router waited → Act stage not reached


def test_ensure_opening_balance_seeds_once_only(dbs):
    assert ensure_opening_balance(dbs, 5000.0) is True
    assert ensure_opening_balance(dbs, 5000.0) is False          # never double-deposit
    assert ensure_opening_balance(dbs, 0.0) is False             # 0 = no-op
    with connection(dbs.portfolio) as conn:
        n = conn.execute("SELECT COUNT(*) FROM ledger WHERE type='DEPOSIT'").fetchone()[0]
    assert n == 1


# ================= A2 — Measure → Learn =================

def test_measure_learn_resolves_round_trip_and_updates_base_rate(dbs):
    """A recorded decision whose position round-trips to a gain resolves to a win and updates the
    strategy's persistent base-rate (L1)."""
    eid = record_trade_decision(dbs, "AAPL", ["quality_momentum"])
    apply_fill(dbs.portfolio, "AAPL", "buy", 10, 100.0)
    apply_fill(dbs.portfolio, "AAPL", "sell", 10, 120.0)         # +200 realized → closed, a WIN
    out = resolve_and_learn(dbs)

    assert out["resolved"] == 1 and out["round_trips"] == 1
    e = get_entry(dbs.learning, eid)
    assert e["actual_outcome"] and "round_trip_pnl" in e["actual_outcome"]
    assert e["mistake_type"] == "OK"
    upd = {s["strategy_id"]: s for s in out["strategies_updated"]}
    assert upd["quality_momentum"]["n"] == 1
    assert upd["quality_momentum"]["base_rate"] >= 0.5           # one win nudges the prior up


def test_resolution_is_idempotent_across_ticks(dbs):
    """A resolved decision is never re-counted (actual_outcome IS NULL filter)."""
    record_trade_decision(dbs, "AAPL", ["core_dca"])
    apply_fill(dbs.portfolio, "AAPL", "buy", 1, 100.0)
    apply_fill(dbs.portfolio, "AAPL", "sell", 1, 110.0)
    assert resolve_and_learn(dbs)["resolved"] == 1
    assert resolve_and_learn(dbs)["resolved"] == 0              # second pass resolves nothing new


def test_open_position_does_not_resolve(dbs):
    """A still-open position (no round-trip) is not resolved — you can't learn from an unfinished trade."""
    record_trade_decision(dbs, "AAPL", ["core_dca"])
    apply_fill(dbs.portfolio, "AAPL", "buy", 1, 100.0)          # bought, never sold → still open
    assert resolve_and_learn(dbs)["resolved"] == 0


def test_systematic_underperformance_files_propose_only_request(dbs):
    """≥20 losing round-trips below the prior base-rate → an L3 proposal lands as 'pending'. And there is
    NO agent-callable apply path: the agent proposes, the founder disposes."""
    for i in range(25):
        sym = f"L{i}"
        record_trade_decision(dbs, sym, ["loser_strat"])
        apply_fill(dbs.portfolio, sym, "buy", 1, 100.0)
        apply_fill(dbs.portfolio, sym, "sell", 1, 90.0)        # loss → realized < 0, closed
    out = resolve_and_learn(dbs)

    assert out["resolved"] == 25
    pend = ip.list_pending(dbs)
    assert any(p["strategy_id"] == "loser_strat" and p["status"] == "pending" for p in pend)
    # PROPOSE-ONLY hard wall: the learning engine cannot apply its own proposals.
    assert not hasattr(ip, "apply") and not hasattr(ip, "auto_apply")


# ----- QA regressions: per-round-trip P&L (not cumulative) + one outcome per close -----

def test_loss_after_win_same_symbol_is_labeled_loss(dbs):
    """A losing round-trip AFTER a winning one is recorded as a LOSS (round-trip P&L, not lifetime
    cumulative) and pulls the base-rate DOWN — the early-warning the cumulative-P&L bug would suppress."""
    s = "alpha"
    e1 = record_trade_decision(dbs, "AAPL", [s])                # baseline 0
    apply_fill(dbs.portfolio, "AAPL", "buy", 10, 100.0)
    apply_fill(dbs.portfolio, "AAPL", "sell", 10, 200.0)        # +1000 → WIN, closed
    out1 = resolve_and_learn(dbs)
    up1 = {x["strategy_id"]: x for x in out1["strategies_updated"]}[s]
    assert up1["base_rate"] == 1.0 and get_entry(dbs.learning, e1)["mistake_type"] == "OK"

    e2 = record_trade_decision(dbs, "AAPL", [s])                # baseline = +1000 (cumulative at open)
    apply_fill(dbs.portfolio, "AAPL", "buy", 10, 100.0)
    apply_fill(dbs.portfolio, "AAPL", "sell", 10, 80.0)         # -200 leg; LIFETIME cumulative still +800
    out2 = resolve_and_learn(dbs)
    e2row = get_entry(dbs.learning, e2)
    assert e2row["mistake_type"] != "OK"                        # NOT mislabeled a win
    assert "round_trip_pnl=-200" in e2row["actual_outcome"]
    up2 = {x["strategy_id"]: x for x in out2["strategies_updated"]}[s]
    assert up2["base_rate"] < 1.0                               # the loss nudged the base-rate down


def test_same_symbol_two_decisions_one_close_counts_once(dbs):
    """Two open decisions for one symbol (DCA re-buys) resolved by a SINGLE close contribute exactly ONE
    win/loss to the strategy sample — not two (no over-count of one economic round-trip)."""
    s = "dca"
    d1 = record_trade_decision(dbs, "AAPL", [s])                # baseline 0
    apply_fill(dbs.portfolio, "AAPL", "buy", 10, 100.0)
    d2 = record_trade_decision(dbs, "AAPL", [s])                # baseline 0 (still open, no realized yet)
    apply_fill(dbs.portfolio, "AAPL", "buy", 10, 100.0)         # qty 20, avg 100
    apply_fill(dbs.portfolio, "AAPL", "sell", 20, 120.0)        # +400, closed
    out = resolve_and_learn(dbs)
    assert out["resolved"] == 2 and out["round_trips"] == 1     # 2 decision rows, ONE economic close
    up = {x["strategy_id"]: x for x in out["strategies_updated"]}[s]
    assert up["n"] == 1                                          # ONE outcome, not two
    assert get_entry(dbs.learning, d1)["actual_outcome"] and get_entry(dbs.learning, d2)["actual_outcome"]


def test_break_even_round_trip_is_not_a_phantom_loss(dbs):
    """A zero-P&L close (true break-even, or a decision recorded against an already-flat symbol) is marked
    resolved but contributes NO win/loss to the base-rate — never a phantom loss (QA re-verify finding)."""
    eid = record_trade_decision(dbs, "AAPL", ["flat"])
    apply_fill(dbs.portfolio, "AAPL", "buy", 10, 100.0)
    apply_fill(dbs.portfolio, "AAPL", "sell", 10, 100.0)        # break-even → realized 0, closed
    out = resolve_and_learn(dbs)
    assert out["round_trips"] == 1
    assert get_entry(dbs.learning, eid)["actual_outcome"]       # resolved (idempotent next pass)
    assert all(s["strategy_id"] != "flat" for s in out["strategies_updated"])   # n stays 0, no phantom loss


def test_end_to_end_buy_close_resolve_updates_base_rate(dbs):
    """The S16 Gate through real components: buy via the assembled loop + real PaperBroker (durable Act),
    record the decision (Measure), close the position, then resolve_and_learn → a resolved learning row and
    a non-zero base-rate delta. (The governed auto-SELL generator is S16-A7; here the close is explicit.)"""
    broker = PaperBroker(dbs.portfolio, dbs.market, allow_fallback_price=True)   # fills at $1
    loop = AssembledLoop(dbs, broker_execute=lambda a: broker.submit(a, Decision(allow=True, reason="ok")))
    r = loop.run_tick([_buy("AAPL", notional=50.0)], _state(), edge_reports={"AAPL": _pass_edge("AAPL")})
    assert "AAPL" in r.executed and held_qty(dbs.portfolio, "AAPL") > 0

    record_trade_decision(dbs, "AAPL", ["e2e"])                 # Measure (as run_trading_tick does)
    apply_fill(dbs.portfolio, "AAPL", "sell", held_qty(dbs.portfolio, "AAPL"), 2.0)   # close at a gain
    out = resolve_and_learn(dbs)

    assert out["round_trips"] == 1
    up = {x["strategy_id"]: x for x in out["strategies_updated"]}.get("e2e")
    assert up is not None and up["n"] == 1 and up["base_rate"] != 0.5   # base-rate moved off the seed


# ================= S16 review fixes (run lifecycle) =================

class _BadRegistry:
    """A registry whose signal generation blows up — to prove the tick fails cleanly."""
    def signals_for(self, ctx, portfolio_id=None):
        raise RuntimeError("signals boom")


def test_tick_failure_marks_run_error_not_stuck_running(dbs, tmp_path):
    """If the governed body raises, the runs row is finished as 'error' — never left stuck 'running'
    with ended_at NULL forever (review bug #1)."""
    with pytest.raises(RuntimeError):
        run_trading_tick(dbs, symbols=["AAPL"], config_path=_write_yaml(tmp_path, 0),
                         registry=_BadRegistry())
    with connection(dbs.portfolio) as conn:
        row = conn.execute("SELECT outcome, ended_at FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    assert row["outcome"] == "error" and row["ended_at"] is not None


def test_wait_and_halted_ticks_do_not_advance_readiness_clock(dbs, tmp_path):
    """No-op ticks must NOT advance the ≥28-run live-readiness gate (review bug #2): an unfunded book
    routes to 'wait' (outcome 'no_action') and a kill-switched tick is 'halted' — neither counts."""
    from ops.live_readiness import _paper_runs
    from ops.kill_switch import halt, resume
    cfg = _write_yaml(tmp_path, 0)

    for _ in range(3):                                       # unfunded book → router 'wait'
        out = run_trading_tick(dbs, symbols=["AAPL"], config_path=cfg)
        assert out["outcome"] == "no_action" and out["executed"] == []

    halt()                                                  # kill switch on → 'halted'
    try:
        out = run_trading_tick(dbs, symbols=["AAPL"], config_path=cfg)
        assert out["outcome"] == "halted"
    finally:
        resume()

    # ops/live_readiness counts WHERE outcome LIKE 'complete%' — none of these no-op/halted ticks qualify
    assert _paper_runs(dbs) == 0

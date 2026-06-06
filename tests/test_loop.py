"""
Sprint 3 — Loop runner tests.  Uses dbs fixture (7-DB architecture).
LoopConfig now takes dbs: CamelDbs instead of db_path: str.
"""
import sqlite3
import pytest
from db.paths import CamelDbs
from loop.runner import LoopConfig, LoopRunner
from loop.state import begin_run, finish_run
from guardrail.constitution import (
    Action, ActionType, Instrument, PortfolioState, Thesis,
)
from ops.kill_switch import halt, resume, is_halted


@pytest.fixture(autouse=True)
def clear_kill_switch():
    resume()
    yield
    resume()


def minimal_cfg(dbs: CamelDbs, **hooks) -> LoopConfig:
    return LoopConfig(dbs=dbs, **hooks)


# ─────────────────── happy path ─────────────────────────────────

def test_loop_completes_all_steps(dbs):
    state = LoopRunner(minimal_cfg(dbs)).run_once()
    assert state.outcome == "complete"
    statuses = {s.name: s.status for s in state.steps}
    for step in ("observe", "thesis", "choose", "act", "measure", "learn"):
        assert statuses[step] == "ok", f"step '{step}' not ok"

def test_loop_persists_run_to_db(dbs):
    LoopRunner(minimal_cfg(dbs)).run_once()
    with sqlite3.connect(dbs.portfolio) as conn:
        row = conn.execute(
            "SELECT outcome FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row and row[0] == "complete"

def test_loop_run_id_assigned(dbs):
    state = LoopRunner(minimal_cfg(dbs)).run_once()
    assert state.run_id is not None and state.run_id > 0

def test_multiple_runs_each_get_own_row(dbs):
    runner = LoopRunner(minimal_cfg(dbs))
    runner.run_once()
    runner.run_once()
    with sqlite3.connect(dbs.portfolio) as conn:
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert count == 2


# ─────────────────── kill switch ────────────────────────────────

def test_kill_switch_halts_loop(dbs):
    halt()
    state = LoopRunner(minimal_cfg(dbs)).run_once()
    assert state.outcome == "halted"

def test_kill_switch_halted_loop_writes_no_run_row(dbs):
    halt()
    LoopRunner(minimal_cfg(dbs)).run_once()
    with sqlite3.connect(dbs.portfolio) as conn:
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert count == 0


# ─────────────────── Constitution gate inside Act ────────────────

def _compliant_state():
    wl = {"SPUS": Instrument("SPUS", sector="Diversified",
                              sharia_status="compliant", on_whitelist=True)}
    return PortfolioState(fund_usd=10_000, cash_usd=5_000, whitelist=wl)

def _off_list_state():
    return PortfolioState(fund_usd=10_000, cash_usd=5_000, whitelist={})

def test_good_action_allowed_in_act(dbs):
    good = Action(type=ActionType.TRADE, symbol="SPUS", side="buy",
                  notional_usd=500, instrument_type="etf",
                  thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"),
                  mode="paper")
    executed = []
    cfg = LoopConfig(dbs=dbs,
                     generate_theses=lambda obs: [good],
                     choose=lambda t: t,
                     get_portfolio_state=_compliant_state,
                     execute_order=lambda a, d: executed.append(a))
    LoopRunner(cfg).run_once()
    assert len(executed) == 1

def test_bad_action_blocked_in_act(dbs):
    bad = Action(type=ActionType.TRADE, symbol="TSLA", side="buy",
                 notional_usd=500, instrument_type="equity",
                 thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"),
                 mode="paper")
    executed = []
    cfg = LoopConfig(dbs=dbs,
                     generate_theses=lambda obs: [bad],
                     choose=lambda t: t,
                     get_portfolio_state=_off_list_state,
                     execute_order=lambda a, d: executed.append(a))
    state = LoopRunner(cfg).run_once()
    assert state.outcome == "complete" and executed == []

def test_act_records_block_in_state(dbs):
    bad = Action(type=ActionType.TRADE, symbol="TSLA", side="buy",
                 notional_usd=500, instrument_type="equity",
                 thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"),
                 mode="paper")
    cfg = LoopConfig(dbs=dbs,
                     generate_theses=lambda obs: [bad],
                     choose=lambda t: t,
                     get_portfolio_state=_off_list_state)
    state = LoopRunner(cfg).run_once()
    results = state.step("act").detail["results"]
    assert results[0]["allowed"] is False


# ─────────────────── error recovery ─────────────────────────────

def test_observe_error_marks_step_and_finishes(dbs):
    cfg = LoopConfig(dbs=dbs, observe=lambda: (_ for _ in ()).throw(RuntimeError("down")))
    state = LoopRunner(cfg).run_once()
    assert state.outcome == "error" and state.step("observe").status == "error"

def test_measure_error_does_not_abort_loop(dbs):
    cfg = LoopConfig(dbs=dbs,
                     measure=lambda: (_ for _ in ()).throw(RuntimeError("unavailable")))
    state = LoopRunner(cfg).run_once()
    assert state.step("measure").status == "error"
    assert state.step("learn").status == "ok"
    assert state.outcome == "complete"

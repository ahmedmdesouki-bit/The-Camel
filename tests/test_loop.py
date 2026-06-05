"""
Sprint 3 — Loop runner tests.
Gate: full loop runs, all steps recorded, Constitution blocks bad actions,
kill switch halts, state persists across calls.
"""
import sqlite3
import pytest
from db.sqlite import init_db
from loop.runner import LoopConfig, LoopRunner
from loop.state import begin_run, finish_run
from guardrail.constitution import (
    Action, ActionType, Instrument, PortfolioState, Thesis,
)
from ops.kill_switch import halt, resume, is_halted


@pytest.fixture(autouse=True)
def clear_kill_switch():
    """Ensure kill switch is off for every test."""
    resume()
    yield
    resume()


@pytest.fixture
def tmp_db(tmp_path):
    db = str(tmp_path / "adam.db")
    init_db(db)
    return db


def minimal_cfg(tmp_db, **hooks) -> LoopConfig:
    return LoopConfig(db_path=tmp_db, **hooks)


# ─────────────────── happy path ─────────────────────────────────

def test_loop_completes_all_steps(tmp_db):
    cfg = minimal_cfg(tmp_db)
    state = LoopRunner(cfg).run_once()
    assert state.outcome == "complete"
    statuses = {s.name: s.status for s in state.steps}
    for step in ("observe", "thesis", "choose", "act", "measure", "learn"):
        assert statuses[step] == "ok", f"step '{step}' not ok: {statuses[step]}"

def test_loop_persists_run_to_db(tmp_db):
    LoopRunner(minimal_cfg(tmp_db)).run_once()
    with sqlite3.connect(tmp_db) as conn:
        row = conn.execute(
            "SELECT outcome FROM runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
    assert row and row[0] == "complete"

def test_loop_run_id_assigned(tmp_db):
    state = LoopRunner(minimal_cfg(tmp_db)).run_once()
    assert state.run_id is not None and state.run_id > 0

def test_multiple_runs_each_get_own_row(tmp_db):
    runner = LoopRunner(minimal_cfg(tmp_db))
    runner.run_once()
    runner.run_once()
    with sqlite3.connect(tmp_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    assert count == 2


# ─────────────────── kill switch ────────────────────────────────

def test_kill_switch_halts_loop(tmp_db):
    halt()
    state = LoopRunner(minimal_cfg(tmp_db)).run_once()
    assert state.outcome == "halted"

def test_kill_switch_halted_loop_writes_no_run_row(tmp_db):
    halt()
    LoopRunner(minimal_cfg(tmp_db)).run_once()
    with sqlite3.connect(tmp_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    # halted before begin_run — no row written
    assert count == 0


# ─────────────────── Constitution gate inside Act ────────────────

def _compliant_state():
    wl = {"SPUS": Instrument("SPUS", sector="Diversified",
                              sharia_status="compliant", on_whitelist=True)}
    return PortfolioState(fund_usd=10_000, cash_usd=5_000, whitelist=wl)

def _off_list_state():
    return PortfolioState(fund_usd=10_000, cash_usd=5_000, whitelist={})

def test_good_action_allowed_in_act(tmp_db):
    good_action = Action(
        type=ActionType.TRADE, symbol="SPUS", side="buy",
        notional_usd=500, instrument_type="etf",
        thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"),
        mode="paper",
    )
    executed = []
    cfg = LoopConfig(
        db_path=tmp_db,
        generate_theses=lambda obs: [good_action],
        choose=lambda t: t,
        get_portfolio_state=_compliant_state,
        execute_order=lambda a, d: executed.append(a),
    )
    LoopRunner(cfg).run_once()
    assert len(executed) == 1

def test_bad_action_blocked_in_act(tmp_db):
    bad_action = Action(
        type=ActionType.TRADE, symbol="TSLA", side="buy",
        notional_usd=500, instrument_type="equity",
        thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"),
        mode="paper",
    )
    executed = []
    cfg = LoopConfig(
        db_path=tmp_db,
        generate_theses=lambda obs: [bad_action],
        choose=lambda t: t,
        get_portfolio_state=_off_list_state,
        execute_order=lambda a, d: executed.append(a),
    )
    state = LoopRunner(cfg).run_once()
    assert state.outcome == "complete"
    assert executed == []   # blocked, never executed

def test_act_records_block_in_state(tmp_db):
    bad_action = Action(
        type=ActionType.TRADE, symbol="TSLA", side="buy",
        notional_usd=500, instrument_type="equity",
        thesis=Thesis(invalidation="x", profit_take="y", time_stop="z"),
        mode="paper",
    )
    cfg = LoopConfig(
        db_path=tmp_db,
        generate_theses=lambda obs: [bad_action],
        choose=lambda t: t,
        get_portfolio_state=_off_list_state,
    )
    state = LoopRunner(cfg).run_once()
    act_step = state.step("act")
    assert act_step.status == "ok"
    results = act_step.detail["results"]
    assert results[0]["allowed"] is False


# ─────────────────── error recovery ─────────────────────────────

def test_observe_error_marks_step_and_finishes(tmp_db):
    def boom():
        raise RuntimeError("data source down")

    cfg = LoopConfig(db_path=tmp_db, observe=boom)
    state = LoopRunner(cfg).run_once()
    assert state.outcome == "error"
    assert state.step("observe").status == "error"

def test_measure_error_does_not_abort_loop(tmp_db):
    def broken_measure():
        raise RuntimeError("metrics unavailable")

    cfg = LoopConfig(db_path=tmp_db, measure=broken_measure)
    state = LoopRunner(cfg).run_once()
    # measure error is recorded but loop still reaches learn + complete
    assert state.step("measure").status == "error"
    assert state.step("learn").status == "ok"
    assert state.outcome == "complete"

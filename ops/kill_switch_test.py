"""
Kill-switch self-test (S5.5) — confirm a halt stops the next loop tick and resume restores.

S6 schedules this weekly; here it is the runnable routine. It exercises the real LoopRunner:
halted → outcome 'halted' and no new run row; resumed → outcome 'complete'.
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass, field
from typing import Dict

from db.paths import NoahDbs
from loop.runner import LoopConfig, LoopRunner
from ops.kill_switch import halt, resume, is_halted


@dataclass
class KillSwitchTestResult:
    passed: bool
    detail: Dict[str, str] = field(default_factory=dict)


def _run_count(portfolio_db: str) -> int:
    with sqlite3.connect(portfolio_db) as conn:
        return conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]


def run_kill_switch_test(dbs: NoahDbs) -> KillSwitchTestResult:
    detail: Dict[str, str] = {}
    resume()  # ensure a clean start

    runner = LoopRunner(LoopConfig(dbs=dbs))

    # 1) halted → loop must NOT run a tick
    before = _run_count(dbs.portfolio)
    halt()
    halted_state = runner.run_once()
    after_halt = _run_count(dbs.portfolio)
    detail["halted_outcome"] = halted_state.outcome
    detail["halted_wrote_run"] = str(after_halt != before)

    # 2) resumed → loop completes
    resume()
    resumed_state = runner.run_once()
    detail["resumed_outcome"] = resumed_state.outcome
    detail["kill_switch_off_after"] = str(not is_halted())

    passed = (
        halted_state.outcome == "halted"
        and after_halt == before                 # no run row written while halted
        and resumed_state.outcome == "complete"
        and not is_halted()
    )
    return KillSwitchTestResult(passed=passed, detail=detail)

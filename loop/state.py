"""
Loop run state — persisted to the SQLite runs table.
Every step is recorded so the loop can resume cleanly after a crash.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, List, Optional

from db.sqlite import connection

STEPS = ("observe", "thesis", "choose", "act", "measure", "learn")


@dataclass
class StepRecord:
    name: str
    status: str = "pending"     # pending | ok | skipped | error
    detail: Any = None
    error: Optional[str] = None


@dataclass
class RunState:
    run_id: Optional[int] = None
    started_at: str = ""
    phase: int = 0
    steps: List[StepRecord] = field(
        default_factory=lambda: [StepRecord(s) for s in STEPS]
    )
    outcome: str = "running"    # running | complete | error | halted

    def step(self, name: str) -> StepRecord:
        for s in self.steps:
            if s.name == name:
                return s
        raise ValueError(f"Unknown step: {name!r}")

    def mark(self, name: str, status: str, detail: Any = None,
             error: Optional[str] = None) -> None:
        s = self.step(name)
        s.status = status
        s.detail = detail
        s.error = error

    def to_steps_json(self) -> str:
        return json.dumps([
            {"name": s.name, "status": s.status,
             "detail": s.detail, "error": s.error}
            for s in self.steps
        ])


def _ensure_table(db_path: str) -> None:
    # Canonical schema for `runs` lives in db/portfolio.py; this defensive
    # CREATE IF NOT EXISTS only lets the loop run before init_all() has been called.
    with connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                started_at  TEXT,
                ended_at    TEXT,
                phase       INTEGER,
                steps_json  TEXT,
                outcome     TEXT
            )
        """)


def begin_run(db_path: str, phase: int = 0) -> RunState:
    _ensure_table(db_path)
    now = datetime.now(timezone.utc).isoformat()
    state = RunState(phase=phase, started_at=now)
    with connection(db_path) as conn:
        cur = conn.execute(
            "INSERT INTO runs (started_at, phase, steps_json, outcome) VALUES (?,?,?,?)",
            (now, phase, state.to_steps_json(), "running"),
        )
        state.run_id = cur.lastrowid
    return state


def update_run(db_path: str, state: RunState) -> None:
    with connection(db_path) as conn:
        conn.execute(
            "UPDATE runs SET steps_json=?, outcome=? WHERE id=?",
            (state.to_steps_json(), state.outcome, state.run_id),
        )


def finish_run(db_path: str, state: RunState, outcome: str = "complete") -> None:
    state.outcome = outcome
    with connection(db_path) as conn:
        conn.execute(
            "UPDATE runs SET ended_at=?, steps_json=?, outcome=? WHERE id=?",
            (datetime.now(timezone.utc).isoformat(),
             state.to_steps_json(), outcome, state.run_id),
        )

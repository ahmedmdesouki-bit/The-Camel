"""
S17.7 — desk pause/resume control (the Kitchen's grip on the workforce).

The founder can pause a desk from the Kitchen; the Workforce skips a paused desk (returns a 'paused'
DeskResult, runs nothing). The web only REQUESTS a pause through the founder-only command channel — this
brain-side module is what actually writes the control state. Defaults to NOT paused (a desk runs unless
explicitly paused).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

from db.paths import CamelDbs
from db.sqlite import connection


def _ensure(learning_db: str) -> None:
    with connection(learning_db) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS desk_control ("
            " desk_id TEXT PRIMARY KEY, paused INTEGER DEFAULT 0, updated_at TEXT, updated_by TEXT)")


def set_paused(dbs: CamelDbs, desk_id: str, paused: bool, by: str = "founder") -> None:
    _ensure(dbs.learning)
    with connection(dbs.learning) as conn:
        conn.execute(
            "INSERT INTO desk_control (desk_id, paused, updated_at, updated_by) VALUES (?,?,?,?) "
            "ON CONFLICT(desk_id) DO UPDATE SET paused=excluded.paused, updated_at=excluded.updated_at, "
            "updated_by=excluded.updated_by",
            (desk_id, 1 if paused else 0, datetime.now(timezone.utc).isoformat(), by))


def is_paused(dbs: CamelDbs, desk_id: str) -> bool:
    try:
        with connection(dbs.learning) as conn:
            r = conn.execute("SELECT paused FROM desk_control WHERE desk_id=?", (desk_id,)).fetchone()
        return bool(r and r["paused"])
    except Exception:                                         # no control table yet → nothing is paused
        return False


def all_control(dbs: CamelDbs) -> Dict[str, bool]:
    _ensure(dbs.learning)
    with connection(dbs.learning) as conn:
        rows = conn.execute("SELECT desk_id, paused FROM desk_control").fetchall()
    return {r["desk_id"]: bool(r["paused"]) for r in rows}

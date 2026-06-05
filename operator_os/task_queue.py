"""
Persistent task queue (S5) — every planned action is enqueued before execution, so intent
is auditable and the operator can pause/resume. Backed by the `tasks` table (noah_portfolio.db,
canonical schema in db/portfolio.py).
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from db.sqlite import connection

VALID_STATUS = ("pending", "running", "done", "failed")


def enqueue(portfolio_db: str, task_type: str, payload: Optional[Dict[str, Any]] = None) -> int:
    with connection(portfolio_db) as conn:
        cur = conn.execute(
            "INSERT INTO tasks (task_type, payload, status) VALUES (?, ?, 'pending')",
            (task_type, json.dumps(payload or {})),
        )
        return cur.lastrowid


def list_pending(portfolio_db: str) -> List[Dict]:
    with connection(portfolio_db) as conn:
        rows = conn.execute(
            "SELECT * FROM tasks WHERE status='pending' ORDER BY id ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def next_task(portfolio_db: str) -> Optional[Dict]:
    pend = list_pending(portfolio_db)
    return pend[0] if pend else None


def set_status(portfolio_db: str, task_id: int, status: str) -> None:
    if status not in VALID_STATUS:
        raise ValueError(f"invalid status {status!r}")
    with connection(portfolio_db) as conn:
        conn.execute(
            "UPDATE tasks SET status=?, updated_at=? WHERE id=?",
            (status, datetime.now(timezone.utc).isoformat(), task_id),
        )


def get_task(portfolio_db: str, task_id: int) -> Optional[Dict]:
    with connection(portfolio_db) as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    return dict(row) if row else None

"""
Append-only operator action log (S5) — separate from the trade ledger.

Records every state transition, tool invocation, and router decision so the operator's
behaviour is fully auditable. Backed by `op_log` (noah_portfolio.db).
"""
from __future__ import annotations
import json
from typing import Any, Dict, List

from db.sqlite import connection


def append(portfolio_db: str, event_type: str, detail: Any = None) -> int:
    payload = detail if isinstance(detail, str) else json.dumps(detail or {})
    with connection(portfolio_db) as conn:
        cur = conn.execute(
            "INSERT INTO op_log (event_type, detail) VALUES (?, ?)",
            (event_type, payload),
        )
        return cur.lastrowid


def tail(portfolio_db: str, n: int = 20) -> List[Dict]:
    with connection(portfolio_db) as conn:
        rows = conn.execute(
            "SELECT * FROM op_log ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(r) for r in rows]

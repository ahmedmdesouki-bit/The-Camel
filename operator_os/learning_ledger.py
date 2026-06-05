"""
Learning Ledger (S5) — the shared memory of both arms.

Records every consequential decision with its expected outcome; later, the actual outcome,
mistake classification, and lesson are written back. This is how Noah learns across trading,
products, research, and system-building. Backed by `learning_ledger` (noah_learning.db).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Dict, List, Optional

from db.sqlite import connection

# decision_type: TRADE | PRODUCT | RESEARCH | WAIT | SYSTEM | EDGE_PROOF
# mistake_type:  SIGNAL_ERROR | SIZING_ERROR | TIMING_ERROR | SHARIA_DRIFT | OK | NULL


def record_decision(
    learning_db: str,
    decision_type: str,
    thesis_summary: str,
    expected_outcome: str = "",
    ref: str = "",
) -> int:
    with connection(learning_db) as conn:
        cur = conn.execute(
            "INSERT INTO learning_ledger "
            "(decision_type, thesis_summary, expected_outcome, ref) VALUES (?,?,?,?)",
            (decision_type, thesis_summary, expected_outcome, ref),
        )
        return cur.lastrowid


def record_outcome(
    learning_db: str,
    entry_id: int,
    actual_outcome: str,
    mistake_type: str = "OK",
    lesson_learned: str = "",
    rule_update_recommendation: str = "",
    reusable_pattern: str = "",
) -> None:
    with connection(learning_db) as conn:
        conn.execute(
            "UPDATE learning_ledger SET actual_outcome=?, outcome_measured_at=?, "
            "mistake_type=?, lesson_learned=?, rule_update_recommendation=?, "
            "reusable_pattern=? WHERE id=?",
            (actual_outcome, datetime.now(timezone.utc).isoformat(), mistake_type,
             lesson_learned, rule_update_recommendation, reusable_pattern, entry_id),
        )


def get_entry(learning_db: str, entry_id: int) -> Optional[Dict]:
    with connection(learning_db) as conn:
        row = conn.execute(
            "SELECT * FROM learning_ledger WHERE id=?", (entry_id,)
        ).fetchone()
    return dict(row) if row else None


def list_lessons(learning_db: str) -> List[Dict]:
    """Resolved entries that carry a lesson (the accumulated wisdom)."""
    with connection(learning_db) as conn:
        rows = conn.execute(
            "SELECT * FROM learning_ledger WHERE lesson_learned IS NOT NULL "
            "AND lesson_learned != '' ORDER BY id ASC"
        ).fetchall()
    return [dict(r) for r in rows]

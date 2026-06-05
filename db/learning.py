"""
Learning DB — noah_learning.db
Stores: every Noah decision with its expected + actual outcome,
mistake classification, lesson, and reusable pattern.
This is the shared learning ledger for Trader and Entrepreneur arms.
"""
import sqlite3

DDL = """
CREATE TABLE IF NOT EXISTS learning_ledger (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                          TEXT DEFAULT (datetime('now')),
    decision_type               TEXT,   -- TRADE | PRODUCT | RESEARCH | WAIT
    thesis_summary              TEXT,
    expected_outcome            TEXT,
    actual_outcome              TEXT,
    outcome_measured_at         TEXT,
    mistake_type                TEXT,   -- SIGNAL_ERROR | SIZING_ERROR | TIMING_ERROR | SHARIA_DRIFT | OK | NULL
    lesson_learned              TEXT,
    rule_update_recommendation  TEXT,
    reusable_pattern            TEXT,
    ref                         TEXT    -- order_id or run_id
);
"""


def init_learning_db(path: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(DDL)

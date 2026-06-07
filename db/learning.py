"""
Learning DB — camel_learning.db
Stores: every Camel decision with its expected + actual outcome,
mistake classification, lesson, and reusable pattern.
This is the shared learning ledger for Trader and Entrepreneur arms.
"""
from db.sqlite import connection

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

-- S10: full 17-check Edge Proof reports (the decision-quality audit trail).
CREATE TABLE IF NOT EXISTS edge_reports (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                              TEXT DEFAULT (datetime('now')),
    symbol                          TEXT,
    signal                          TEXT,
    signal_definition_hash          TEXT,
    sample_size                     INTEGER,
    regime_filtered_sample_size     INTEGER,
    hit_rate                        REAL,
    median_excess_return            REAL,
    worst_forward_return            REAL,
    max_drawdown                    REAL,
    benchmark                       TEXT,
    after_costs                     REAL,
    turnover_estimate               REAL,
    data_quality_score              REAL,
    multiple_testing_penalty_applied INTEGER,
    signal_decay_detected           INTEGER,
    mode                            TEXT,        -- shadow | enforcing
    would_allow                     INTEGER,
    trade_allowed                   INTEGER,
    reason                          TEXT,
    checks_json                     TEXT
);

-- S11 (L3): the learning engine PROPOSES changes here; it never auto-applies them. A human (L4)
-- approves out-of-band. status: pending | approved | rejected.
CREATE TABLE IF NOT EXISTS learning_proposals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT DEFAULT (datetime('now')),
    proposal_type   TEXT,        -- activate | deactivate | regime_affinity | weight_band | ...
    strategy_id     TEXT,
    detail          TEXT,        -- JSON
    rationale       TEXT,
    status          TEXT DEFAULT 'pending',
    decided_by      TEXT,
    decided_at      TEXT
);
"""


def init_learning_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

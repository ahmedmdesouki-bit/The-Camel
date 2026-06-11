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

-- S16 (L1 persistence): per-strategy hit-rate prior + sample, updated by the Learn step after trades
-- resolve. A NUMBER store ONLY (base_rate + counts) — it never touches a rule, a weight band, or the
-- Constitution (those stay founder-owned, L4). This is what makes the autonomy ladder evidence-backed.
CREATE TABLE IF NOT EXISTS strategy_base_rates (
    strategy_id   TEXT PRIMARY KEY,
    base_rate     REAL DEFAULT 0.5,
    n             INTEGER DEFAULT 0,
    wins          INTEGER DEFAULT 0,
    losses        INTEGER DEFAULT 0,
    updated_at    TEXT
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

-- S17.6: the Opportunity Board — the CONDUCTOR's ranked, reasoned, governed PROPOSALS ("where to put the
-- money"). Each row carries its full reason chain. A proposal is a PROPOSAL only: nothing here executes —
-- acting on one still flows through the governed tick (Edge Proof → Constitution → Budget → Approval).
CREATE TABLE IF NOT EXISTS opportunity_proposals (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                  TEXT DEFAULT (datetime('now')),
    symbol              TEXT,
    action              TEXT,        -- buy | dca | wait | avoid
    score               REAL,
    regime              TEXT,
    sharia_status       TEXT,
    edge_allowed        INTEGER,
    hit_rate            REAL,
    sample_size         INTEGER,
    confidence          REAL,
    recommended_action  TEXT,
    invalidation        TEXT,
    reason_chain        TEXT,        -- JSON list of human-readable reasons (the evidence chain)
    status              TEXT DEFAULT 'proposed',   -- proposed | approved | vetoed | expired
    founder_rank        REAL,        -- S17.7 founder reorder override (NULL = use computed score)
    decided_by          TEXT,
    decided_at          TEXT
);

-- S17.7: desk pause/resume control (the Kitchen). The Workforce skips a paused desk. Founder-owned;
-- the web only REQUESTS a pause via the command channel — the brain writes this row.
CREATE TABLE IF NOT EXISTS desk_control (
    desk_id     TEXT PRIMARY KEY,
    paused      INTEGER DEFAULT 0,
    updated_at  TEXT,
    updated_by  TEXT
);

-- S17.1: the Workforce audit log — one row per desk run (history; the Kitchen derives current desk
-- status from the latest row per desk_id). Append-only operational telemetry; carries no trade power.
CREATE TABLE IF NOT EXISTS desk_runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT DEFAULT (datetime('now')),
    desk_id     TEXT,
    status      TEXT,        -- ok | empty | error
    summary     TEXT,
    metrics     TEXT,        -- JSON
    evidence_n  INTEGER DEFAULT 0,
    started_at  TEXT,
    ended_at    TEXT,
    error       TEXT
);

-- S12.5: the Research Desk writes EVIDENCE here and only here. It can never act — there is no
-- execute path. Evidence flows into Edge Proof; it never bypasses a gate. The desk's master switch
-- defaults OFF (dormant until capital + proven edge justify the token spend).
CREATE TABLE IF NOT EXISTS research_evidence (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                      TEXT DEFAULT (datetime('now')),
    desk                    TEXT,        -- which vertical desk produced it
    claim                   TEXT,
    scope                   TEXT,        -- instrument / portfolio / sector
    evidence_ids            TEXT,        -- JSON array of source_document ids
    source_count            INTEGER,
    freshness               TEXT,
    disagreement_score      REAL,
    confidence              REAL,
    horizon                 TEXT,
    direction               TEXT,        -- positive | negative | neutral
    invalidation_conditions TEXT,
    recommended_action      TEXT,        -- a PROPOSAL only — never executed
    portfolio_fit           TEXT,
    compliance_status       TEXT,
    known_at                TEXT
);

-- S17.5: append-only consolidated operational-memory digests (desk reliability + detected patterns).
-- Canonical home (was previously created only ad-hoc by research/memory.py). Read-only telemetry.
CREATE TABLE IF NOT EXISTS memory_consolidation (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT DEFAULT (datetime('now')),
    summary TEXT
);

-- Hot-path indexes for the audit/telemetry queries that currently scan.
CREATE INDEX IF NOT EXISTS idx_learning_ledger_type ON learning_ledger(decision_type);
CREATE INDEX IF NOT EXISTS idx_opportunity_proposals_status ON opportunity_proposals(status);
CREATE INDEX IF NOT EXISTS idx_desk_runs_desk ON desk_runs(desk_id, id);
CREATE INDEX IF NOT EXISTS idx_edge_reports_symbol ON edge_reports(symbol);
"""


def init_learning_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

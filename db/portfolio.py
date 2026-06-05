"""
Portfolio DB — noah_portfolio.db
Stores: orders (with client_order_id), positions, ledger, runs,
guardrail_events, approvals.
Extended schema per Feedback 1: client_order_id on orders.
"""
from db.sqlite import connection

DDL = """
CREATE TABLE IF NOT EXISTS orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    client_order_id TEXT UNIQUE,
    symbol          TEXT,
    side            TEXT,
    qty             REAL,
    type            TEXT DEFAULT 'market',
    limit_price     REAL,
    status          TEXT,
    broker          TEXT DEFAULT 'paper',
    mode            TEXT DEFAULT 'paper',
    approval_id     TEXT,
    thesis_id       TEXT,
    created_at      TEXT,
    filled_at       TEXT,
    fill_price      REAL
);

CREATE TABLE IF NOT EXISTS positions (
    symbol          TEXT PRIMARY KEY,
    qty             REAL,
    avg_cost        REAL,
    market_value    REAL,
    unrealized_pnl  REAL,
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ledger (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              TEXT,
    type            TEXT,
    symbol          TEXT,
    amount          REAL,
    balance_after   REAL,
    ref             TEXT,
    hash            TEXT
);

CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT,
    ended_at    TEXT,
    phase       INTEGER,
    steps_json  TEXT,
    outcome     TEXT
);

CREATE TABLE IF NOT EXISTS guardrail_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT DEFAULT (datetime('now')),
    action_json TEXT,
    decision    INTEGER,
    reason      TEXT,
    limit_hit   TEXT
);

CREATE TABLE IF NOT EXISTS approvals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    action_ref  TEXT,
    status      TEXT DEFAULT 'pending',
    requested_at TEXT DEFAULT (datetime('now')),
    decided_at  TEXT,
    decided_by  TEXT,
    channel     TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type   TEXT,
    payload     TEXT,                              -- JSON
    status      TEXT DEFAULT 'pending',            -- pending | running | done | failed
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT
);

CREATE TABLE IF NOT EXISTS op_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT DEFAULT (datetime('now')),
    event_type  TEXT,                              -- STATE_TRANSITION | TOOL_CALL | ROUTER | ...
    detail      TEXT
);
"""


def init_portfolio_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

"""
Portfolio DB — camel_portfolio.db
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
    qty             REAL    DEFAULT 0,
    avg_cost        REAL    DEFAULT 0,
    market_price    REAL    DEFAULT 0,
    market_value    REAL    DEFAULT 0,
    unrealized_pnl  REAL    DEFAULT 0,
    realized_pnl    REAL    DEFAULT 0,        -- S6.6: realized on sells
    opened_at       TEXT,
    updated_at      TEXT    DEFAULT (datetime('now')),
    status          TEXT    DEFAULT 'open'    -- open | closed
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

CREATE TABLE IF NOT EXISTS heartbeat (
    id          INTEGER PRIMARY KEY CHECK (id = 1),  -- single row
    ts          TEXT
);

-- S11: multi-portfolio layer under the single Camel Fund.
CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id             TEXT PRIMARY KEY,
    name                     TEXT,
    mandate                  TEXT,
    phase                    TEXT,        -- incubate|qualify|pilot|scale|defend|retire
    benchmark                TEXT,
    target_weight            REAL,        -- share of the fund
    cash_min_pct             REAL,
    gross_exposure_limit_pct REAL,
    max_drawdown_pct         REAL,
    turnover_budget_pct      REAL,
    assigned_strategies      TEXT,        -- JSON array of strategy ids
    sharia_policy_version    TEXT,
    updated_at               TEXT
);

CREATE TABLE IF NOT EXISTS portfolio_holdings (
    portfolio_id    TEXT,
    symbol          TEXT,
    qty             REAL DEFAULT 0,
    avg_cost        REAL DEFAULT 0,
    market_value    REAL DEFAULT 0,
    updated_at      TEXT,
    PRIMARY KEY (portfolio_id, symbol)
);
"""


def init_portfolio_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

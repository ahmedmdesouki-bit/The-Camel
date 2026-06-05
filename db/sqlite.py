"""
SQLite schema initialiser — Phase 0 local DB.
Single init_db(path) call creates all tables needed by sharia/ and data/.
Mirrors the Postgres schema in db/schema.sql but speaks SQLite.
"""
import sqlite3


DDL = """
CREATE TABLE IF NOT EXISTS whitelist (
    symbol       TEXT PRIMARY KEY,
    asset_type   TEXT DEFAULT 'etf',
    sharia_status TEXT DEFAULT 'unknown',
    frozen       INTEGER DEFAULT 0,
    approved_by  TEXT,
    scanned_at   TEXT,
    scan_id      TEXT,
    source       TEXT
);

CREATE TABLE IF NOT EXISTS sharia_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT DEFAULT (datetime('now')),
    event_type TEXT,
    symbol     TEXT,
    reason     TEXT,
    detail     TEXT
);

CREATE TABLE IF NOT EXISTS prices (
    symbol      TEXT,
    date        TEXT,
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    volume      INTEGER,
    adj_close   REAL,
    source      TEXT,
    ingested_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (symbol, date, source)
);

CREATE TABLE IF NOT EXISTS guardrail_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT DEFAULT (datetime('now')),
    action_json TEXT,
    decision    INTEGER,
    reason      TEXT,
    limit_hit   TEXT
);
"""


def init_db(path: str) -> None:
    """Create all Phase-0 tables. Safe to call on an existing DB."""
    with sqlite3.connect(path) as conn:
        conn.executescript(DDL)


def connect(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

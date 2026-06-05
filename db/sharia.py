"""
Sharia DB — noah_sharia.db
Stores: versioned whitelist, sharia_events audit log.
Extended schema per Feedback 1: historical_drift_count, purification_ratio,
trigger_period, reasoning_summary.
"""
import sqlite3

DDL = """
CREATE TABLE IF NOT EXISTS whitelist (
    symbol                  TEXT PRIMARY KEY,
    asset_type              TEXT DEFAULT 'etf',
    sharia_status           TEXT DEFAULT 'unknown',
    frozen                  INTEGER DEFAULT 0,
    approved_by             TEXT,
    scanned_at              TEXT,
    scan_id                 TEXT,
    source                  TEXT,
    historical_drift_count  INTEGER DEFAULT 0,
    purification_ratio      REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS sharia_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                  TEXT DEFAULT (datetime('now')),
    event_type          TEXT,
    symbol              TEXT,
    reason              TEXT,
    detail              TEXT,
    trigger_period      TEXT,
    reasoning_summary   TEXT
);
"""


def init_sharia_db(path: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(DDL)

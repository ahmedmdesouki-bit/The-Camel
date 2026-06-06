"""
Sharia DB — camel_sharia.db
Stores: versioned whitelist, sharia_events audit log, ETF holdings (S8 look-through).
Extended schema per Feedback 1: historical_drift_count, purification_ratio,
trigger_period, reasoning_summary.
"""
from db.sqlite import connection
from data.provenance import SOURCE_DOCUMENTS_DDL

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

-- S8: compliant-ETF constituents (look-through to single-name exposure; feeds S9)
CREATE TABLE IF NOT EXISTS etf_holdings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    etf                 TEXT,        -- the ETF symbol (SPUS / HLAL / MNZL)
    holding_ticker      TEXT,
    holding_name        TEXT,
    weight              REAL,        -- % of net assets
    shares              REAL,
    event_date          TEXT,        -- holdings as-of date
    reported_at         TEXT,
    ingested_at         TEXT,
    known_at            TEXT,
    source_id           TEXT,
    source_url          TEXT,
    source_document_id  TEXT,
    content_hash        TEXT,
    parser_version      TEXT,
    data_quality_score  REAL,
    UNIQUE(source_id, etf, holding_ticker, event_date)
);
""" + SOURCE_DOCUMENTS_DDL


def init_sharia_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

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

-- S9 slice 4: append-only multi-state Sharia status (in-house AAOIFI screen × canonical cross-check).
-- One row per screen; the latest row (by id) is current. final_status ∈ pass|fail|doubtful|frozen|
-- pending_review. `authority` records the resolved authority stack (local_board > AAOIFI > founder).
CREATE TABLE IF NOT EXISTS sharia_status (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol              TEXT,
    in_house_status     TEXT,
    cross_check_status  TEXT,
    final_status        TEXT,
    methodology         TEXT,
    authority           TEXT,
    confidence          REAL,
    ratios              TEXT,        -- JSON: debt/liquid-assets/receivables/haram-income ratios
    purification_ratio  REAL,
    sector              TEXT,
    drift               INTEGER DEFAULT 0,
    screened_at         TEXT,
    known_at            TEXT,
    next_review_at      TEXT,
    source_hash         TEXT
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
    -- P2-B: reported_at in the key so a re-stated holdings vintage (same as-of date, later
    -- publish/correction) is INSERTed as a new row rather than silently INSERT-OR-IGNOREd away.
    UNIQUE(source_id, etf, holding_ticker, event_date, reported_at)
);

-- S17: OFAC SDN sanctions snapshot — a sanctioned entity never enters the tradeable universe.
-- Canonical home (was previously created only ad-hoc by sharia/sanctions.py).
CREATE TABLE IF NOT EXISTS sanctions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ent_num     TEXT,
    name        TEXT,
    normalized  TEXT,
    sdn_type    TEXT,
    program     TEXT,
    source      TEXT DEFAULT 'ofac',
    ingested_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sanctions_norm ON sanctions(normalized);

-- Hot path: the latest Sharia status per symbol (sharia_status WHERE symbol=? ORDER BY id DESC).
CREATE INDEX IF NOT EXISTS idx_sharia_status_symbol ON sharia_status(symbol);
""" + SOURCE_DOCUMENTS_DDL


def init_sharia_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

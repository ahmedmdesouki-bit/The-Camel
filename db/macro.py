"""
Macro DB — camel_macro.db  (S8: real point-in-time observations + provenance)
Stores: rates, inflation, GDP, PMIs, yield curve, credit spreads, USD index,
commodity proxies, recession indicators.
Point-in-time snapshots to avoid look-ahead bias in backtesting.
"""
from db.sqlite import connection
from data.provenance import SOURCE_DOCUMENTS_DDL

DDL = """
CREATE TABLE IF NOT EXISTS macro_snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT,
    indicator   TEXT,
    value       REAL,
    source      TEXT,
    period      TEXT,
    region      TEXT DEFAULT 'US'
);

-- S8: point-in-time observations from registered connectors (e.g. FRED/ALFRED)
CREATE TABLE IF NOT EXISTS macro_observations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    series_id           TEXT,
    indicator           TEXT,
    region              TEXT DEFAULT 'US',
    value               REAL,
    event_date          TEXT,    -- when the value is for
    reported_at         TEXT,    -- when it was published (ALFRED vintage)
    ingested_at         TEXT,
    known_at            TEXT,
    source_id           TEXT,
    source_url          TEXT,
    source_document_id  TEXT,
    content_hash        TEXT,
    parser_version      TEXT,
    data_quality_score  REAL,
    UNIQUE(source_id, series_id, event_date, reported_at)
);

-- S9: regime classifications over time (append-only audit of the regime engine's calls)
CREATE TABLE IF NOT EXISTS regime_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    classified_at   TEXT,
    regime          TEXT,
    confidence      REAL,
    signals         TEXT,    -- JSON array
    features        TEXT     -- JSON object
);

-- Hot path: the regime feature builder reads macro_observations WHERE series_id=? on every classification.
-- The UNIQUE(source_id, series_id, …) index can't serve a series_id-leading lookup, so add an explicit one.
CREATE INDEX IF NOT EXISTS idx_macro_obs_series ON macro_observations(series_id, event_date);
""" + SOURCE_DOCUMENTS_DDL


def init_macro_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

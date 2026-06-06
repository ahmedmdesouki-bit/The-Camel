"""
Fundamentals DB — camel_fundamentals.db  (S8: XBRL company facts + provenance)
Stores: revenue, margins, EPS, FCF, debt, cash, capex,
guidance, valuation multiples, filing dates, risk factor changes.
"""
from db.sqlite import connection
from data.provenance import SOURCE_DOCUMENTS_DDL

DDL = """
CREATE TABLE IF NOT EXISTS fundamentals (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol          TEXT,
    period          TEXT,
    revenue         REAL,
    gross_margin    REAL,
    operating_margin REAL,
    eps             REAL,
    free_cash_flow  REAL,
    total_debt      REAL,
    cash            REAL,
    capex           REAL,
    filing_date     TEXT,
    source          TEXT,
    ingested_at     TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS valuation_snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol      TEXT,
    date        TEXT,
    pe_ratio    REAL,
    pb_ratio    REAL,
    ps_ratio    REAL,
    ev_ebitda   REAL,
    source      TEXT
);

-- S8: point-in-time XBRL facts from SEC EDGAR, fully provenanced
CREATE TABLE IF NOT EXISTS company_facts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cik                 TEXT,
    symbol              TEXT,
    concept             TEXT,    -- e.g. Revenues, Assets
    unit                TEXT,    -- e.g. USD
    value               REAL,
    fiscal_year         INTEGER,
    fiscal_period       TEXT,    -- FY | Q1 | Q2 | ...
    form                TEXT,    -- 10-K | 10-Q | 8-K
    event_date          TEXT,    -- period end
    reported_at         TEXT,    -- filing date
    ingested_at         TEXT,
    known_at            TEXT,
    source_id           TEXT,
    source_url          TEXT,
    source_document_id  TEXT,    -- accession number
    content_hash        TEXT,
    parser_version      TEXT,
    data_quality_score  REAL,
    UNIQUE(source_id, cik, concept, event_date, source_document_id)
);
""" + SOURCE_DOCUMENTS_DDL


def init_fundamentals_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

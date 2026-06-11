"""
Market Data DB — camel_market.db
Stores: prices, (future) dividends, splits, ETF holdings, market cap.

Point-in-time columns (S4): event_date / reported_at / ingested_at / known_at let
backtests see only what was knowable at the decision time (no look-ahead bias).
See docs/CAMEL_DATA_CONTRACTS.md. Added now, before data accumulates — cannot be retrofitted.
"""
from db.sqlite import connection
from data.provenance import SOURCE_DOCUMENTS_DDL

DDL = """
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
    event_date  TEXT,                              -- when the bar's session occurred
    reported_at TEXT,                              -- when the data vendor published it
    ingested_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),    -- when Camel collected it
    known_at    TEXT,                              -- when Camel was allowed to use it
    PRIMARY KEY (symbol, date, source)
);

CREATE TABLE IF NOT EXISTS dividends (
    symbol      TEXT,
    ex_date     TEXT,
    amount      REAL,
    source      TEXT,
    PRIMARY KEY (symbol, ex_date)
);

CREATE TABLE IF NOT EXISTS splits (
    symbol      TEXT,
    split_date  TEXT,
    ratio       REAL,
    source      TEXT,
    PRIMARY KEY (symbol, split_date)
);
""" + SOURCE_DOCUMENTS_DDL


def init_market_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

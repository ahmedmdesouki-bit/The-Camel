"""
Market Data DB — noah_market.db
Stores: prices, (future) dividends, splits, ETF holdings, market cap.
"""
from db.sqlite import connection

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
    ingested_at TEXT DEFAULT (datetime('now')),
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
"""


def init_market_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

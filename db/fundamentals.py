"""
Fundamentals DB — noah_fundamentals.db  [Sprint 7 stub]
Stores: revenue, margins, EPS, FCF, debt, cash, capex,
guidance, valuation multiples, filing dates, risk factor changes.
"""
import sqlite3

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
"""


def init_fundamentals_db(path: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(DDL)

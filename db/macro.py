"""
Macro DB — camel_macro.db  [Sprint 7 stub]
Stores: rates, inflation, GDP, PMIs, yield curve, credit spreads, USD index,
commodity proxies, recession indicators.
Point-in-time snapshots to avoid look-ahead bias in backtesting.
"""
from db.sqlite import connection

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
"""


def init_macro_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

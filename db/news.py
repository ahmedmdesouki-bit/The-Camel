"""
News/Events DB — camel_news.db  [Sprint 7 stub]
Stores structured event objects — never raw web text.
Raw strings are sanitised to JSON via data/sanitiser.py before landing here.
"""
from db.sqlite import connection

DDL = """
CREATE TABLE IF NOT EXISTS news_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    date                TEXT,
    event_type          TEXT,
    region              TEXT,
    affected_assets     TEXT,       -- JSON array
    severity            INTEGER,    -- 1-5
    expected_duration   TEXT,       -- short | medium | long
    source_count        INTEGER,
    confidence          REAL,
    event_summary       TEXT,
    raw_source_url      TEXT,
    ingested_at         TEXT DEFAULT (datetime('now'))
);
"""


def init_news_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

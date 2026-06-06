"""
News/Events DB — camel_news.db  (S8: structured, provenanced events — never raw web text)

Connectors store STRUCTURED event objects only. Titles/snippets pass through data/sanitiser.py;
injection-flagged content is REDACTED and marked unsafe (safe=0) before it is ever stored, so no
hostile string persists in a field the reasoning engine could read. S9 fills the synthesis columns
(affected_assets, severity, direction, confidence) on top of these rows.
"""
from db.sqlite import connection
from data.provenance import SOURCE_DOCUMENTS_DDL

DDL = """
CREATE TABLE IF NOT EXISTS news_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id            TEXT,
    event_type          TEXT,        -- news_article | filing_8k | ...
    title               TEXT,        -- SANITISED (redacted if injection-flagged)
    url                 TEXT,
    domain              TEXT,
    language            TEXT,
    source_country      TEXT,
    region              TEXT,
    affected_assets     TEXT,        -- JSON array (S9 synthesis)
    tone                REAL,
    severity            INTEGER,
    direction           TEXT,
    confidence          REAL,
    safe                INTEGER DEFAULT 1,   -- 0 = injection-flagged content
    event_date          TEXT,
    reported_at         TEXT,
    ingested_at         TEXT,
    known_at            TEXT,
    source_id           TEXT,
    source_url          TEXT,
    source_document_id  TEXT,
    content_hash        TEXT,
    parser_version      TEXT,
    data_quality_score  REAL,
    UNIQUE(source_id, event_id)
);
""" + SOURCE_DOCUMENTS_DDL


def init_news_db(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(DDL)

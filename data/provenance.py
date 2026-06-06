"""
Provenance enforcement (S8) — no decision-relevant record without full lineage.

Every record a connector stores must carry where it came from, when it happened, when it was
reported, when we ingested it, and when we were *allowed* to use it (the point-in-time quadruple),
plus a content hash + parser version so a parse can be re-derived and audited. A record missing any
provenance field is not decision-grade and must be dropped (or raise).

The `source_documents` table records the raw document we fetched (one row per URL), so a stored fact
can always be traced back to the bytes it came from.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import List

from db.sqlite import connection

# fields every stored, decision-relevant record must carry
PROVENANCE_FIELDS = (
    "source_id", "source_url", "source_document_id", "content_hash", "parser_version",
    "event_date",     # when it happened
    "reported_at",    # when the public learned it
    "ingested_at",    # when Camel collected it
    "known_at",       # when Camel was allowed to use it
    "data_quality_score",
)

SOURCE_DOCUMENTS_DDL = """
CREATE TABLE IF NOT EXISTS source_documents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id           TEXT,
    source_url          TEXT,
    source_document_id  TEXT,
    content_hash        TEXT,
    parser_version      TEXT,
    fetched_at          TEXT,
    license_status      TEXT DEFAULT 'unknown',
    UNIQUE(source_id, source_document_id, content_hash)
);
"""


def init_source_documents(path: str) -> None:
    with connection(path) as conn:
        conn.executescript(SOURCE_DOCUMENTS_DDL)


def content_hash(raw) -> str:
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def missing_provenance(rec: dict) -> List[str]:
    """Return the provenance fields that are absent or empty in `rec`."""
    out = []
    for f in PROVENANCE_FIELDS:
        v = rec.get(f, None)
        if v is None or (isinstance(v, str) and not v.strip()):
            out.append(f)
    return out


class ProvenanceError(ValueError):
    """Raised when a record is stored without complete provenance."""


def assert_provenanced(rec: dict) -> None:
    miss = missing_provenance(rec)
    if miss:
        raise ProvenanceError(f"record missing provenance: {', '.join(miss)}")


@dataclass
class SourceDocument:
    source_id: str
    source_url: str
    source_document_id: str
    content_hash: str
    parser_version: str
    fetched_at: str
    license_status: str = "unknown"


def record_source_document(path: str, doc: SourceDocument) -> None:
    """Write the fetched document's provenance row (idempotent on the content hash)."""
    with connection(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO source_documents "
            "(source_id, source_url, source_document_id, content_hash, parser_version, fetched_at, license_status) "
            "VALUES (?,?,?,?,?,?,?)",
            (doc.source_id, doc.source_url, doc.source_document_id, doc.content_hash,
             doc.parser_version, doc.fetched_at, doc.license_status),
        )

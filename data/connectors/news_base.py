"""
NewsConnector (S8) — shared store + the hostile-text discipline for event connectors.

Raw external text is hostile by default. `make_event` runs every title through data/sanitiser.py;
if any injection pattern is present the title is **redacted** (the raw string is never stored) and the
event is marked `safe=0` with a low data-quality score so downstream (Edge Proof / router) distrusts it.
Only structured fields land in `news_events` — there is no column for a raw article body.
"""
from __future__ import annotations
import hashlib
from typing import List

from db.sqlite import connection
from data.connectors.base import SourceConnector
from data.sanitiser import sanitise

_REDACTED = "[redacted: injection-flagged content]"


class NewsConnector(SourceConnector):

    def make_event(self, *, title: str, url: str, event_date: str,
                   event_type: str = "news_article", **extra) -> dict:
        s = sanitise(title or "")
        event_id = hashlib.sha256(f"{self.spec.source_id}:{url}".encode()).hexdigest()[:32]
        rec = {
            "event_id": event_id,
            "event_type": event_type,
            "title": s.clean_text if s.safe else _REDACTED,   # never store the raw hostile string
            "url": url,
            "event_date": event_date,
            "safe": 1 if s.safe else 0,
            "data_quality_score": 0.85 if s.safe else 0.3,    # flagged content is low-trust
        }
        rec.update(extra)
        return rec

    def store(self, db: str, records: List[dict]) -> int:
        n = 0
        with connection(db) as conn:
            for r in records:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO news_events "
                    "(event_id, event_type, title, url, domain, language, source_country, tone, "
                    " direction, safe, event_date, reported_at, ingested_at, known_at, source_id, "
                    " source_url, source_document_id, content_hash, parser_version, data_quality_score) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["event_id"], r["event_type"], r["title"], r.get("url"), r.get("domain"),
                     r.get("language"), r.get("source_country"), r.get("tone"), r.get("direction"),
                     r.get("safe", 1), r["event_date"], r["reported_at"], r["ingested_at"],
                     r["known_at"], r["source_id"], r["source_url"], r["source_document_id"],
                     r["content_hash"], r["parser_version"], r["data_quality_score"]),
                )
                n += cur.rowcount
        return n

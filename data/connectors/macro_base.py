"""
MacroConnector (S8) — shared `store` for any connector that writes point-in-time macro observations.

A macro connector only implements `urls(**params)` and `parse(raw, url)`; the parsed records carry
series_id / indicator / value / event_date (region optional). This base writes them — fully
provenance-stamped by SourceConnector — into `macro_observations`, idempotently.
"""
from __future__ import annotations
from typing import List

from db.sqlite import connection
from data.connectors.base import SourceConnector


class MacroConnector(SourceConnector):
    def store(self, db: str, records: List[dict]) -> int:
        n = 0
        with connection(db) as conn:
            for r in records:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO macro_observations "
                    "(series_id, indicator, region, value, event_date, reported_at, ingested_at, "
                    " known_at, source_id, source_url, source_document_id, content_hash, "
                    " parser_version, data_quality_score) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["series_id"], r["indicator"], r.get("region", "US"), r["value"],
                     r["event_date"], r["reported_at"], r["ingested_at"], r["known_at"],
                     r["source_id"], r["source_url"], r["source_document_id"], r["content_hash"],
                     r["parser_version"], r["data_quality_score"]),
                )
                n += cur.rowcount
        return n

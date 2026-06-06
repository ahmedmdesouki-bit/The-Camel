"""
FRED connector (S8) — macro series observations → camel_macro.db.

Uses the FRED observations API (JSON). When ALFRED vintage fields are present (`realtime_start`),
they populate `reported_at`, giving honest point-in-time macro. Missing FRED values ('.') are skipped.
Network only via the injected transport; tests pass canned JSON.
"""
from __future__ import annotations
import os
from urllib.parse import urlencode, urlparse, parse_qs
from typing import List

from db.sqlite import connection
from data.connectors.base import SourceConnector
from data.source_registry import FRED


class FredConnector(SourceConnector):
    spec = FRED
    parser_version = "fred.v1"

    def urls(self, series_id: str, api_key: str = None, **_) -> List[str]:
        key = api_key or os.environ.get("FRED_API_KEY", "")
        q = urlencode({"series_id": series_id, "api_key": key, "file_type": "json"})
        return [f"{self.spec.base_url}/series/observations?{q}"]

    def parse(self, raw: str, url: str) -> List[dict]:
        series_id = parse_qs(urlparse(url).query).get("series_id", [""])[0]
        data = self.parse_json(raw)
        out = []
        for obs in data.get("observations", []):
            val = obs.get("value")
            if val in (None, "", "."):          # FRED missing-value marker
                continue
            rec = {
                "series_id": series_id, "indicator": series_id,
                "value": float(val), "event_date": obs.get("date"),
            }
            if obs.get("realtime_start"):       # ALFRED vintage → real reported_at
                rec["reported_at"] = obs["realtime_start"]
            out.append(rec)
        return out

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

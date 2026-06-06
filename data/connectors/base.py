"""
SourceConnector base (S8) — the shared fetch → parse → normalize → validate → store pipeline.

The HTTP layer is an **injectable transport** (`Callable[[str], str]`): production uses a stdlib
`urllib` fetch; unit tests inject a stub returning canned payloads, so **no test ever hits the live
web** — same guarantee as recorded cassettes, with zero extra dependencies.

A connector implements three things:
  - `urls(**params)`  → the list of URLs to fetch,
  - `parse(raw, url)` → data-only dicts (it may set event_date / reported_at / source_document_id),
  - `store(db, records)` → write the structured rows (records arrive fully provenance-stamped).
The base handles provenance stamping, validation (drop anything not fully provenanced), and the
`source_documents` audit row per fetched URL.
"""
from __future__ import annotations
import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from data.source_registry import SourceSpec
from data.provenance import (
    SourceDocument, content_hash, missing_provenance, record_source_document,
)

Transport = Callable[[str], str]

# A polite default User-Agent; SEC in particular requires a contact (overridden per connector).
DEFAULT_HEADERS = {"User-Agent": "TheCamel/0.1 (personal research; contact: founder@example.com)"}


def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 20.0) -> str:
    """Stdlib HTTP GET → text. The only place that touches the network (never called in tests)."""
    req = urllib.request.Request(url, headers=headers or DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:   # noqa: S310 (trusted, registered sources)
        return resp.read().decode("utf-8")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunResult:
    source_id: str
    fetched: int      # records parsed
    stored: int       # records written
    dropped: int      # records dropped for missing provenance
    documents: int    # source_documents written


class SourceConnector:
    spec: SourceSpec
    parser_version: str = "v1"
    headers: Optional[Dict[str, str]] = None     # connector-specific (e.g. SEC UA)

    # ---- to be implemented by each connector ----
    def urls(self, **params) -> List[str]:
        raise NotImplementedError

    def parse(self, raw: str, url: str) -> List[dict]:
        raise NotImplementedError

    def store(self, db: str, records: List[dict]) -> int:
        raise NotImplementedError

    # ---- shared pipeline ----
    def default_transport(self) -> Transport:
        hdrs = self.headers or DEFAULT_HEADERS
        return lambda url: http_get(url, headers=hdrs)

    @staticmethod
    def parse_json(raw: str) -> dict:
        return json.loads(raw)

    def _stamp(self, rec: dict, raw: str, url: str, now: str) -> dict:
        r = dict(rec)
        r["event_date"] = r.get("event_date") or now
        r["reported_at"] = r.get("reported_at") or r["event_date"]
        r["ingested_at"] = now
        r["known_at"] = now                         # Phase 0: known when ingested
        r["source_id"] = self.spec.source_id
        r["source_url"] = url
        r["source_document_id"] = r.get("source_document_id") or f"{self.spec.source_id}:{url}"
        r["content_hash"] = content_hash(raw)
        r["parser_version"] = self.parser_version
        r["data_quality_score"] = r.get("data_quality_score", 0.9)
        return r

    def run(self, db: str, transport: Optional[Transport] = None,
            now: Optional[str] = None, **params) -> RunResult:
        transport = transport or self.default_transport()
        now = now or _utcnow()
        fetched = stored = dropped = documents = 0
        for url in self.urls(**params):
            raw = transport(url)
            record_source_document(db, SourceDocument(
                source_id=self.spec.source_id, source_url=url,
                source_document_id=f"{self.spec.source_id}:{url}",
                content_hash=content_hash(raw), parser_version=self.parser_version,
                fetched_at=now,
            ))
            documents += 1
            stamped = [self._stamp(rec, raw, url, now) for rec in self.parse(raw, url)]
            fetched += len(stamped)
            valid = [r for r in stamped if not missing_provenance(r)]
            dropped += len(stamped) - len(valid)
            stored += self.store(db, valid)
        return RunResult(self.spec.source_id, fetched, stored, dropped, documents)

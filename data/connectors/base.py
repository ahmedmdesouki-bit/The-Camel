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
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from data.source_registry import SourceSpec
from data.provenance import (
    SourceDocument, content_hash, missing_provenance, record_source_document,
)

Transport = Callable[[str], str]

# A polite, descriptive default User-Agent. Several free sources (SEC, GDELT, FRED) block or rate-limit
# generic/empty agents, so we identify ourselves honestly with a contact. SEC requires this per its policy.
DEFAULT_HEADERS = {
    "User-Agent": "TheCamel/0.1 (+https://github.com/ahmedmdesouki-bit/The-Camel; personal research; contact: founder@thecamel.local)",
    "Accept-Encoding": "identity",
}

# HTTP statuses worth retrying: 429 (rate limit) + the 5xx transient server-side band.
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


_SECRET_PARAMS = re.compile(r"(?i)\b(api_key|apikey|api-key|token|apiToken|key|secret)=([^&\s]+)")


def redact_url(url: str) -> str:
    """Strip secret query-param VALUES from a URL before it is persisted anywhere (DB rows,
    source_documents, logs). Keys ride in URLs for some vendors (FRED), and persisted rows are
    backed up off-box — a key at rest in camel_macro.db is a leak (S16 QA). The param NAME is kept
    so provenance stays readable; only the value is replaced."""
    return _SECRET_PARAMS.sub(lambda m: f"{m.group(1)}=REDACTED", url or "")


def http_get(url: str, headers: Optional[Dict[str, str]] = None, timeout: float = 20.0) -> str:
    """Stdlib HTTP GET → text. The only place that touches the network (never called in tests)."""
    req = urllib.request.Request(url, headers=headers or DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:   # noqa: S310 (trusted, registered sources)
        return resp.read().decode("utf-8")


def _is_retryable(exc: Exception) -> bool:
    """Transient network failures we should back off and retry, vs. permanent ones (404, 403) we shouldn't."""
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in _RETRYABLE_STATUS
    if isinstance(exc, urllib.error.URLError):
        return True                      # DNS / connection reset / timeout — transient
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    return False


def with_retries(transport: Transport, retries: int = 3, backoff_base: float = 0.5,
                 sleeper: Callable[[float], None] = time.sleep) -> Transport:
    """Wrap any transport with bounded retry + exponential backoff on *transient* failures only.

    Permanent errors (403 Forbidden, 404 Not Found, parse errors) are re-raised immediately — retrying
    them is pointless and rude. `sleeper` is injectable so tests exercise the backoff with zero real wait.
    """
    def _wrapped(url: str) -> str:
        last: Optional[Exception] = None
        for attempt in range(max(1, retries)):
            try:
                return transport(url)
            except Exception as exc:     # noqa: BLE001 — classify, then re-raise if non-transient/exhausted
                last = exc
                if not _is_retryable(exc) or attempt == retries - 1:
                    raise
                sleeper(backoff_base * (2 ** attempt))   # 0.5s, 1s, 2s, ...
        assert last is not None
        raise last
    return _wrapped


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
        return with_retries(lambda url: http_get(url, headers=hdrs))

    @staticmethod
    def parse_json(raw: str) -> dict:
        return json.loads(raw)

    @staticmethod
    def parse_csv(raw: str) -> list:
        """Parse CSV text into a list of dict rows (stdlib; no pandas dependency)."""
        import csv
        import io
        return list(csv.DictReader(io.StringIO(raw)))

    def _stamp(self, rec: dict, raw: str, url: str, now: str) -> dict:
        r = dict(rec)
        # Do NOT fabricate event_date: a record the parser couldn't date is not point-in-time
        # honest, so leave it empty and let validate (missing_provenance) drop it. (Fabricating
        # `now` here also collapsed UNIQUE(... event_date ...) and silently dropped real rows.)
        ed = r.get("event_date")
        r["event_date"] = ed
        r["reported_at"] = r.get("reported_at") or ed
        r["ingested_at"] = now
        r["known_at"] = now                         # Phase 0: known when ingested
        r["source_id"] = self.spec.source_id
        safe_url = redact_url(url)                  # never persist a key at rest (S16 QA)
        r["source_url"] = safe_url
        r["source_document_id"] = r.get("source_document_id") or f"{self.spec.source_id}:{safe_url}"
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
            raw = transport(url)                    # the LIVE fetch needs the real key…
            safe_url = redact_url(url)              # …but nothing persisted at rest may carry it (QA)
            record_source_document(db, SourceDocument(
                source_id=self.spec.source_id, source_url=safe_url,
                source_document_id=f"{self.spec.source_id}:{safe_url}",
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

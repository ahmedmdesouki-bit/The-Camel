"""
S8 — Data Intelligence Backbone (first slice): SourceConnector framework, provenance enforcement,
FRED (macro) + SEC EDGAR (fundamentals) connectors, scraping policy.

Hermetic: the HTTP transport is stubbed with canned payloads — no test hits the live web.
"""
import sqlite3
import pytest

from data.provenance import (
    PROVENANCE_FIELDS, missing_provenance, assert_provenanced, ProvenanceError, content_hash,
)
from data.source_registry import all_specs, get
from data.connectors.fred import FredConnector
from data.connectors.sec_edgar import SecEdgarConnector
from security.scraping_policy import (
    is_allowed, assert_allowed, preferred_method, requires_contact_header, ScrapingPolicyError,
)

NOW = "2026-06-06T00:00:00+00:00"


def _stub(payload: str):
    return lambda url: payload


FRED_JSON = """
{"observations": [
  {"date": "2026-05-01", "value": "4.25", "realtime_start": "2026-05-02", "realtime_end": "9999-12-31"},
  {"date": "2026-06-01", "value": ".",    "realtime_start": "2026-06-02"},
  {"date": "2026-06-01", "value": "4.30", "realtime_start": "2026-06-02"}
]}
"""

SEC_JSON = """
{"cik": 320193, "taxonomy": "us-gaap", "tag": "Revenues", "label": "Revenues", "units": {"USD": [
  {"end": "2025-09-30", "val": 391035000000, "fy": 2025, "fp": "FY", "form": "10-K", "filed": "2025-11-01", "accn": "0000320193-25-000001"},
  {"end": "2024-09-30", "val": 383285000000, "fy": 2024, "fp": "FY", "form": "10-K", "filed": "2024-11-01", "accn": "0000320193-24-000001"}
]}}
"""


# ---------------- provenance enforcement ----------------

def test_missing_provenance_flags_empty_record():
    assert set(missing_provenance({})) == set(PROVENANCE_FIELDS)

def test_full_record_has_no_missing_provenance():
    rec = {f: "x" for f in PROVENANCE_FIELDS}
    rec["data_quality_score"] = 0.9
    assert missing_provenance(rec) == []

def test_assert_provenanced_raises_on_incomplete():
    with pytest.raises(ProvenanceError):
        assert_provenanced({"source_id": "fred"})

def test_content_hash_is_stable():
    assert content_hash("abc") == content_hash(b"abc")


# ---------------- source registry ----------------

def test_registry_lists_official_sources():
    ids = [s.source_id for s in all_specs()]
    assert "fred" in ids and "sec_edgar" in ids
    assert get("sec_edgar").reliability_tier == 1 and not get("sec_edgar").is_paid


# ---------------- FRED connector (macro) ----------------

def test_fred_stores_observations_with_provenance(dbs):
    res = FredConnector().run(dbs.macro, transport=_stub(FRED_JSON), series_id="DGS10", now=NOW)
    assert res.stored == 2 and res.dropped == 0 and res.documents == 1   # the '.' row skipped by parse
    with sqlite3.connect(dbs.macro) as c:
        row = c.execute(
            "SELECT series_id, value, event_date, reported_at, source_id, content_hash, known_at "
            "FROM macro_observations ORDER BY event_date"
        ).fetchone()
    assert row[0] == "DGS10" and row[1] == pytest.approx(4.25)
    assert row[3] == "2026-05-02"                # ALFRED vintage → reported_at
    assert row[4] == "fred" and row[5] and row[6] == NOW

def test_fred_records_source_document(dbs):
    FredConnector().run(dbs.macro, transport=_stub(FRED_JSON), series_id="DGS10", now=NOW)
    with sqlite3.connect(dbs.macro) as c:
        n = c.execute("SELECT COUNT(*) FROM source_documents WHERE source_id='fred'").fetchone()[0]
    assert n == 1

def test_fred_ingestion_is_idempotent(dbs):
    FredConnector().run(dbs.macro, transport=_stub(FRED_JSON), series_id="DGS10", now=NOW)
    res2 = FredConnector().run(dbs.macro, transport=_stub(FRED_JSON), series_id="DGS10", now=NOW)
    assert res2.stored == 0                       # UNIQUE(source,series,event_date,reported_at)
    with sqlite3.connect(dbs.macro) as c:
        total = c.execute("SELECT COUNT(*) FROM macro_observations").fetchone()[0]
    assert total == 2


# ---------------- SEC EDGAR connector (fundamentals) ----------------

def test_sec_stores_company_facts_with_point_in_time(dbs):
    res = SecEdgarConnector().run(dbs.fundamentals, transport=_stub(SEC_JSON),
                                  cik=320193, concept="Revenues", symbol="AAPL", now=NOW)
    assert res.stored == 2 and res.documents == 1
    with sqlite3.connect(dbs.fundamentals) as c:
        r = c.execute(
            "SELECT cik, symbol, concept, value, event_date, reported_at, source_document_id, source_id "
            "FROM company_facts ORDER BY event_date DESC"
        ).fetchone()
    assert r[0] == "0000320193" and r[1] == "AAPL" and r[2] == "Revenues"
    assert r[4] == "2025-09-30" and r[5] == "2025-11-01"          # period end vs filing date
    assert r[6] == "0000320193-25-000001" and r[7] == "sec_edgar"


# ---------------- validate step drops unprovenanced records ----------------

class _BrokenConnector(FredConnector):
    def _stamp(self, rec, raw, url, now):
        r = super()._stamp(rec, raw, url, now)
        r["content_hash"] = ""        # simulate a provenance failure
        return r

def test_run_drops_records_missing_provenance(dbs):
    res = _BrokenConnector().run(dbs.macro, transport=_stub(FRED_JSON), series_id="DGS10", now=NOW)
    assert res.stored == 0 and res.dropped == 2


# ---------------- scraping policy ----------------

def test_browser_is_qa_only():
    assert not is_allowed("browser", "decisioning")
    assert is_allowed("browser", "qa")
    assert is_allowed("api", "decisioning")

def test_preferred_method_picks_the_most_trustworthy():
    assert preferred_method(["static_scrape", "api", "rss"]) == "api"

def test_assert_allowed_blocks_browser_for_decisioning():
    with pytest.raises(ScrapingPolicyError):
        assert_allowed("browser", "decisioning")

def test_sec_requires_contact_header():
    assert requires_contact_header("sec_edgar")

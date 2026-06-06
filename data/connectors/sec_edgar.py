"""
SEC EDGAR connector (S8) — XBRL company facts → camel_fundamentals.db.

Uses the SEC `companyconcept` XBRL API (JSON) for one concept (e.g. Revenues). The filing date
(`filed`) becomes `reported_at` and the period end (`end`) becomes `event_date` — honest
point-in-time fundamentals. SEC requires a descriptive User-Agent with a contact; we set one.
Network only via the injected transport; tests pass canned JSON.
"""
from __future__ import annotations
from typing import List

from db.sqlite import connection
from data.connectors.base import SourceConnector
from data.source_registry import SEC_EDGAR

# SEC fair-access policy: identify yourself with a contact. (Founder sets a real address.)
_SEC_HEADERS = {"User-Agent": "TheCamel/0.1 personal-research founder@example.com",
                "Accept-Encoding": "gzip, deflate"}


class SecEdgarConnector(SourceConnector):
    spec = SEC_EDGAR
    parser_version = "sec_xbrl.v1"
    headers = _SEC_HEADERS

    def urls(self, cik, concept: str = "Revenues", taxonomy: str = "us-gaap",
             symbol: str = "", **_) -> List[str]:
        cik10 = str(cik).zfill(10)
        self._symbol = symbol               # carried into parse for the row
        return [f"{self.spec.base_url}/api/xbrl/companyconcept/CIK{cik10}/{taxonomy}/{concept}.json"]

    def parse(self, raw: str, url: str) -> List[dict]:
        data = self.parse_json(raw)
        cik = str(data.get("cik", "")).zfill(10)
        concept = data.get("tag", "")
        symbol = getattr(self, "_symbol", "") or ""
        out = []
        for unit, entries in (data.get("units") or {}).items():
            for e in entries:
                val = e.get("val")
                if val is None or e.get("end") is None:
                    continue
                out.append({
                    "cik": cik, "symbol": symbol, "concept": concept, "unit": unit,
                    "value": float(val), "fiscal_year": e.get("fy"), "fiscal_period": e.get("fp"),
                    "form": e.get("form"), "event_date": e.get("end"),
                    "reported_at": e.get("filed") or e.get("end"),
                    "source_document_id": e.get("accn"),       # accession number = the document
                })
        return out

    def store(self, db: str, records: List[dict]) -> int:
        n = 0
        with connection(db) as conn:
            for r in records:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO company_facts "
                    "(cik, symbol, concept, unit, value, fiscal_year, fiscal_period, form, "
                    " event_date, reported_at, ingested_at, known_at, source_id, source_url, "
                    " source_document_id, content_hash, parser_version, data_quality_score) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["cik"], r.get("symbol", ""), r["concept"], r["unit"], r["value"],
                     r.get("fiscal_year"), r.get("fiscal_period"), r.get("form"),
                     r["event_date"], r["reported_at"], r["ingested_at"], r["known_at"],
                     r["source_id"], r["source_url"], r["source_document_id"], r["content_hash"],
                     r["parser_version"], r["data_quality_score"]),
                )
                n += cur.rowcount
        return n

"""
ETF issuer holdings connector (S8) — Sharia-ETF constituents → camel_sharia.db.

Reads an issuer's published holdings CSV (SPUS / HLAL / MNZL) and stores the constituents so the
portfolio can look *through* an ETF to its single-name exposure (used by S9 entity resolution and
Sharia work). Header-tolerant: column names are matched case/space-insensitively against known
aliases, so different issuers' CSV layouts all map onto one schema. CSV via stdlib (no pandas).
"""
from __future__ import annotations
import re
from typing import List, Optional, Tuple

from db.sqlite import connection
from data.connectors.base import SourceConnector
from data.source_registry import ETF_HOLDINGS

# aliases must be in NORMALISED form (lowercase, alphanumerics only) to match _norm(header)
_TICKER = ("ticker", "stockticker", "holdingticker", "symbol")
_NAME = ("name", "securityname", "companyname", "holdingname", "security", "description")
_WEIGHT = ("weight", "weighting", "ofnetassets", "percentofnetassets", "weightpct")
_SHARES = ("shares", "quantity", "sharesheld")


def _norm(k: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (k or "").lower())


def _pick(row: dict, aliases: Tuple[str, ...]) -> Optional[str]:
    for a in aliases:
        if a in row and str(row[a]).strip():
            return str(row[a]).strip()
    return None


def _to_float(v: Optional[str]) -> Optional[float]:
    if v is None:
        return None
    s = re.sub(r"[,%$\s]", "", str(v))
    try:
        return float(s)
    except ValueError:
        return None


class EtfHoldingsConnector(SourceConnector):
    spec = ETF_HOLDINGS
    parser_version = "etf_holdings.v1"

    def urls(self, holdings_url: str, etf: str = "", as_of: str = "", **_) -> List[str]:
        self._etf = (etf or "").upper()
        self._as_of = as_of
        return [holdings_url]

    def parse(self, raw: str, url: str) -> List[dict]:
        out = []
        for row in self.parse_csv(raw):
            norm = {_norm(k): v for k, v in row.items()}
            ticker = _pick(norm, _TICKER)
            if not ticker:
                continue                       # skip header noise / cash rows without a ticker
            rec = {
                "etf": self._etf,
                "holding_ticker": ticker.upper(),
                "holding_name": _pick(norm, _NAME) or "",
                "weight": _to_float(_pick(norm, _WEIGHT)),
                "shares": _to_float(_pick(norm, _SHARES)),
            }
            if self._as_of:
                rec["event_date"] = self._as_of
            out.append(rec)
        return out

    def store(self, db: str, records: List[dict]) -> int:
        n = 0
        with connection(db) as conn:
            for r in records:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO etf_holdings "
                    "(etf, holding_ticker, holding_name, weight, shares, event_date, reported_at, "
                    " ingested_at, known_at, source_id, source_url, source_document_id, content_hash, "
                    " parser_version, data_quality_score) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["etf"], r["holding_ticker"], r["holding_name"], r.get("weight"), r.get("shares"),
                     r["event_date"], r["reported_at"], r["ingested_at"], r["known_at"], r["source_id"],
                     r["source_url"], r["source_document_id"], r["content_hash"], r["parser_version"],
                     r["data_quality_score"]),
                )
                n += cur.rowcount
        return n

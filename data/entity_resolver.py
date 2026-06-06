"""
Entity resolver (S9) — given a ticker, return its full identity across the knowledge graph.

Ties together everything S8 produced:
  - identity (ticker / CIK / ISIN / CUSIP / name / sector, + delisted flag) from `assets`,
  - latest filing from `company_facts` (SEC XBRL),
  - ETF look-through exposure from `etf_holdings` (which compliant ETFs hold this name),
  - Sharia status from the whitelist.

Pure reads across the seven-DB set (via CamelDbs); `register_asset` upserts identity. This is the
"given a ticker, Camel returns identity + sector + Sharia status + filings + ETF exposure" half of the
S9 gate. The regime engine and full multi-state Sharia cross-check are later S9 slices.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from db.sqlite import connection
from db.paths import CamelDbs
from sharia.whitelist import get_instrument


@dataclass
class ResolvedAsset:
    symbol: str
    cik: Optional[str] = None
    name: str = ""
    sector: str = "Unknown"
    isin: Optional[str] = None
    cusip: Optional[str] = None
    sharia_status: str = "unknown"     # from the whitelist; 'unknown' if not screened
    on_whitelist: bool = False
    frozen: bool = False
    delisted: bool = False
    etf_exposure: List[dict] = field(default_factory=list)   # [{etf, weight}]
    latest_filing: Optional[dict] = None                     # {concept, value, event_date, reported_at, form}
    benchmark: str = "SPUS"

    @property
    def known(self) -> bool:
        """True if we have any identity beyond the bare symbol."""
        return bool(self.cik or self.name != "" or self.on_whitelist or self.etf_exposure)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_asset(dbs: CamelDbs, symbol: str, *, cik: str = None, name: str = None,
                   sector: str = None, isin: str = None, cusip: str = None,
                   active_from: str = None, active_to: str = None, delisted: bool = False) -> None:
    """Upsert identity into `assets` (fundamentals DB)."""
    with connection(dbs.fundamentals) as conn:
        conn.execute(
            "INSERT INTO assets (symbol, cik, isin, cusip, name, sector, active_from, active_to, "
            " delisted_flag, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(symbol) DO UPDATE SET "
            "cik=COALESCE(excluded.cik, assets.cik), isin=COALESCE(excluded.isin, assets.isin), "
            "cusip=COALESCE(excluded.cusip, assets.cusip), name=COALESCE(excluded.name, assets.name), "
            "sector=COALESCE(excluded.sector, assets.sector), "
            "active_from=COALESCE(excluded.active_from, assets.active_from), "
            "active_to=COALESCE(excluded.active_to, assets.active_to), "
            "delisted_flag=excluded.delisted_flag, updated_at=excluded.updated_at",
            (symbol.upper(), cik, isin, cusip, name, sector, active_from, active_to,
             1 if delisted else 0, _utcnow()),
        )


def _get_asset(dbs: CamelDbs, symbol: str) -> Optional[dict]:
    with connection(dbs.fundamentals) as conn:
        row = conn.execute("SELECT * FROM assets WHERE symbol=?", (symbol,)).fetchone()
    return dict(row) if row else None


def etf_exposure(dbs: CamelDbs, symbol: str) -> List[dict]:
    """Reverse look-through: which compliant ETFs hold this single name, and at what weight."""
    with connection(dbs.sharia) as conn:
        rows = conn.execute(
            "SELECT etf, weight FROM etf_holdings WHERE holding_ticker=? ORDER BY etf",
            (symbol,),
        ).fetchall()
    return [{"etf": r["etf"], "weight": r["weight"]} for r in rows]


def _latest_filing(dbs: CamelDbs, cik: Optional[str], symbol: str) -> Optional[dict]:
    with connection(dbs.fundamentals) as conn:
        row = None
        if cik:
            row = conn.execute(
                "SELECT concept, value, event_date, reported_at, form, cik FROM company_facts "
                "WHERE cik=? ORDER BY reported_at DESC LIMIT 1", (cik,)).fetchone()
        if row is None:
            row = conn.execute(
                "SELECT concept, value, event_date, reported_at, form, cik FROM company_facts "
                "WHERE symbol=? ORDER BY reported_at DESC LIMIT 1", (symbol,)).fetchone()
    return dict(row) if row else None


def resolve(dbs: CamelDbs, symbol: str) -> ResolvedAsset:
    """Resolve a ticker to its full cross-graph identity."""
    symbol = (symbol or "").upper()
    a = _get_asset(dbs, symbol) or {}
    inst = get_instrument(dbs.sharia, symbol)
    exposure = etf_exposure(dbs, symbol)
    filing = _latest_filing(dbs, a.get("cik"), symbol)
    return ResolvedAsset(
        symbol=symbol,
        cik=a.get("cik") or (filing or {}).get("cik"),
        name=a.get("name") or "",
        sector=a.get("sector") or "Unknown",
        isin=a.get("isin"),
        cusip=a.get("cusip"),
        sharia_status=(inst or {}).get("sharia_status") or "unknown",
        on_whitelist=inst is not None,
        frozen=bool((inst or {}).get("frozen")),
        delisted=bool(a.get("delisted_flag")),
        etf_exposure=exposure,
        latest_filing=filing,
    )

"""
Ingestion orchestrator (S8 completion / Workstream D) — run the connectors into the 7 DBs.

Until now the connectors only `.run()` inside tests; nothing scheduled production ingestion, so the DBs
never populated themselves. This is that missing entrypoint: a small, declarative manifest of IngestJobs
(connector → which DB → params) plus `run_ingestion`, which runs each job best-effort (one connector's
failure records an error but never aborts the others) and returns a per-source summary.

Hermetic: pass an injected `transport` (and `now`) and no live web is touched — the same contract every
connector already honours. In production, `transport=None` lets each connector use its retry-wrapped HTTP.

    python -m data.ingest --symbols SPUS,HLAL --series FEDFUNDS,DGS10
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from db.paths import CamelDbs


@dataclass
class IngestJob:
    connector: object                    # a SourceConnector instance
    db_attr: str                         # which CamelDbs attribute: market|macro|news|sharia|fundamentals
    params: Dict[str, object] = field(default_factory=dict)
    label: str = ""

    @property
    def source_id(self) -> str:
        return getattr(self.connector.spec, "source_id", self.label or "?")


def run_ingestion(dbs: CamelDbs, jobs: List[IngestJob], *,
                  transport: Optional[Callable[[str], str]] = None,
                  now: Optional[str] = None) -> dict:
    """Run every job best-effort. Returns {source_id: {stored, fetched, dropped} | {error}}."""
    results: dict = {}
    for job in jobs:
        db = getattr(dbs, job.db_attr)
        key = job.label or job.source_id
        try:
            rr = job.connector.run(db, transport=transport, now=now, **job.params)
            results[key] = {"stored": rr.stored, "fetched": rr.fetched,
                            "dropped": rr.dropped, "documents": rr.documents}
        except Exception as exc:                          # one bad source must not stop the rest
            results[key] = {"error": str(exc)}
    return results


# ---- default manifest builders (free, no-key sources) ----

def market_price_jobs(symbols: List[str]) -> List[IngestJob]:
    """A Stooq daily-price job per symbol → camel_market.db."""
    from data.connectors.stooq_prices import StooqPriceConnector
    return [IngestJob(StooqPriceConnector(), "market", {"symbol": s}, label=f"stooq:{s}")
            for s in symbols]


def macro_jobs(series: List[str], api_key: str = "") -> List[IngestJob]:
    """A FRED observations job per series → camel_macro.db (needs FRED_API_KEY for live)."""
    from data.connectors.fred import FredConnector
    key = api_key or os.environ.get("FRED_API_KEY", "")
    return [IngestJob(FredConnector(), "macro", {"series_id": s, "api_key": key}, label=f"fred:{s}")
            for s in series]


def sec_filing_jobs(ciks: List[str]) -> List[IngestJob]:
    """An SEC 8-K filings-RSS job per CIK → camel_news.db."""
    from data.connectors.sec_rss import SecRssConnector
    return [IngestJob(SecRssConnector(), "news", {"cik": c}, label=f"sec_rss:{c}") for c in ciks]


def default_jobs(symbols: Optional[List[str]] = None, series: Optional[List[str]] = None,
                 ciks: Optional[List[str]] = None) -> List[IngestJob]:
    """Assemble a default free-source manifest from the given symbols/series/CIKs."""
    jobs: List[IngestJob] = []
    jobs += market_price_jobs(symbols or [])
    jobs += macro_jobs(series or [])
    jobs += sec_filing_jobs(ciks or [])
    return jobs


def main(argv=None) -> int:                               # pragma: no cover - CLI entrypoint
    import argparse
    p = argparse.ArgumentParser(description="The Camel — data ingestion orchestrator")
    p.add_argument("--db-dir", default=os.environ.get("CAMEL_DB_DIR", "."))
    p.add_argument("--symbols", default=os.environ.get("CAMEL_SYMBOLS", ""))
    p.add_argument("--series", default=os.environ.get("CAMEL_SERIES", ""))
    p.add_argument("--ciks", default=os.environ.get("CAMEL_CIKS", ""))
    args = p.parse_args(argv)

    def _split(s):
        return [x.strip() for x in s.split(",") if x.strip()]

    from db.paths import init_all
    dbs = CamelDbs.from_dir(args.db_dir)
    init_all(dbs)
    jobs = default_jobs(_split(args.symbols), _split(args.series), _split(args.ciks))
    print(run_ingestion(dbs, jobs))
    return 0


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main())

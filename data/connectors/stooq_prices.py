"""
Stooq daily-price connector (S8 completion) — free EOD OHLCV → camel_market.db `prices`.

Stooq publishes free daily bars as CSV (`Date,Open,High,Low,Close,Volume`) with no API key. This is the
first production *price* feed, filling the one S8 gap that mattered most: the Edge Proof had no real price
source. Reliability tier 2 + cross-check required — Stooq is a free aggregator, so a paid survivorship-free
feed (Sharadar/EODHD, S15) should corroborate it before any live decision. CSV via stdlib; network only
through the injected transport (tests pass canned CSV → no live web).
"""
from __future__ import annotations
from typing import List, Optional

from db.sqlite import connection
from data.connectors.base import SourceConnector
from data.source_registry import STOOQ


def _f(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class StooqPriceConnector(SourceConnector):
    spec = STOOQ
    parser_version = "stooq.v1"

    def urls(self, symbol: str, stooq_symbol: str = "", **_) -> List[str]:
        # US tickers carry a `.us` suffix on Stooq; allow an explicit override for other venues.
        self._symbol = (symbol or "").upper()
        s = (stooq_symbol or f"{symbol}.us").lower()
        return [f"{self.spec.base_url}/q/d/l/?s={s}&i=d"]

    def parse(self, raw: str, url: str) -> List[dict]:
        out: List[dict] = []
        for row in self.parse_csv(raw):
            # header-tolerant: Stooq uses Title-case keys
            norm = {(k or "").strip().lower(): v for k, v in row.items()}
            date = (norm.get("date") or "").strip()
            close = _f(norm.get("close"))
            if not date or close is None:
                continue                          # skip blanks / "N/D" rows
            out.append({
                "symbol": self._symbol,
                "date": date, "event_date": date,
                "open": _f(norm.get("open")), "high": _f(norm.get("high")),
                "low": _f(norm.get("low")), "close": close,
                "adj_close": close,               # Stooq daily is unadjusted; adj_close := close
                "volume": _f(norm.get("volume")),
            })
        return out

    def store(self, db: str, records: List[dict]) -> int:
        n = 0
        with connection(db) as conn:
            for r in records:
                cur = conn.execute(
                    "INSERT OR IGNORE INTO prices "
                    "(symbol, date, open, high, low, close, volume, adj_close, source, "
                    " event_date, reported_at, ingested_at, known_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["symbol"], r["date"], r.get("open"), r.get("high"), r.get("low"),
                     r["close"], r.get("volume"), r.get("adj_close"), r["source_id"],
                     r["event_date"], r["reported_at"], r["ingested_at"], r["known_at"]),
                )
                n += cur.rowcount
        return n

"""
Alpaca market-data ingestion — the free IEX EOD feed (Phase 0 price source).

Uses the Alpaca **Market Data API** (Trading-API keys: APCA-API-KEY-ID / APCA-API-SECRET-KEY) over **stdlib
urllib** — deliberately NOT the `alpaca-py`/`requests` SDK. Two reasons: (1) it keeps the connector
zero-dependency like every other data connector, and (2) stdlib `urllib` uses the OS (Windows) trust store,
so it works behind an intercepting proxy/firewall that presents a cert `certifi` doesn't carry — exactly the
environment the brain runs in. Returns plain OHLCV dicts and stores them via `data.store.store_price`.

Free "Basic" plan: US stocks & ETFs, IEX feed, daily bars since 2016 (the latest ~15 minutes of real-time
data is withheld — irrelevant for EOD bars). No paid plan required.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from data.store import store_price

SOURCE = "alpaca"
_DATA_URL = "https://data.alpaca.markets/v2/stocks/bars"


def _headers() -> Dict[str, str]:
    key = os.environ.get("ALPACA_API_KEY", "")
    secret = os.environ.get("ALPACA_API_SECRET", "")
    if not key or not secret:
        raise EnvironmentError("ALPACA_API_KEY and ALPACA_API_SECRET must be set in .env")
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret, "Accept": "application/json"}


def fetch_bars(symbols: List[str], start: _dt.date, end: _dt.date, *,
               feed: str = "iex", timeframe: str = "1Day") -> List[Dict]:
    """Pull daily OHLCV bars for `symbols` over [start, end] from Alpaca's IEX feed, following pagination.
    Returns a flat list of {symbol, date, open, high, low, close, volume, adj_close}. Raises on a hard
    HTTP/network error (the caller — `data.ingest.alpaca_backfill` — catches and reports it)."""
    if not symbols:
        return []
    headers = _headers()
    base = {
        "symbols": ",".join(symbols), "timeframe": timeframe,
        "start": start.isoformat(), "end": end.isoformat(),
        "feed": feed, "limit": "10000", "adjustment": "raw", "sort": "asc",
    }
    out: List[Dict] = []
    page_token: Optional[str] = None
    while True:
        params = dict(base)
        if page_token:
            params["page_token"] = page_token
        req = urllib.request.Request(_DATA_URL + "?" + urllib.parse.urlencode(params), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:   # noqa: S310 (trusted Alpaca endpoint)
            payload = json.loads(resp.read().decode("utf-8"))
        for sym, arr in (payload.get("bars") or {}).items():
            for b in (arr or []):
                day = (b.get("t") or "")[:10]                   # "2024-04-02T04:00:00Z" -> "2024-04-02"
                if not day:
                    continue
                out.append({
                    "symbol": sym, "date": day,
                    "open": float(b["o"]), "high": float(b["h"]), "low": float(b["l"]),
                    "close": float(b["c"]), "volume": int(b.get("v") or 0),
                    "adj_close": float(b["c"]),                 # Alpaca daily bars are unadjusted
                })
        page_token = payload.get("next_page_token")
        if not page_token:
            break
    return out


def ingest_daily(db_path: str, symbols: List[str], date: Optional[_dt.date] = None) -> List[Dict]:
    """Fetch and store EOD bars for `symbols` on `date` (default: today). Returns the stored records."""
    end = date or _dt.date.today()
    records = fetch_bars(symbols, start=end, end=end)
    for rec in records:
        store_price(db_path, rec, source=SOURCE)
    return records

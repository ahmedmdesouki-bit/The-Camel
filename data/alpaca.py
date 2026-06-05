"""
Alpaca paper data ingestion.

Adapter pattern: concrete implementation for Alpaca's free paper API.
Stores OHLCV into the local SQLite prices table.

Phase 0 uses Alpaca's free IEX feed.  Upgrade to SIP when breadth requires it.
alpaca-py must be installed (see requirements.txt).
"""
from __future__ import annotations
import os
import datetime
from typing import List, Dict, Optional

from data.store import store_price

SOURCE = "alpaca"


def _client():
    try:
        from alpaca.data import StockHistoricalDataClient  # type: ignore
    except ImportError as e:
        raise ImportError(
            "alpaca-py is not installed.  Run: pip install alpaca-py"
        ) from e

    api_key = os.environ.get("ALPACA_API_KEY", "")
    api_secret = os.environ.get("ALPACA_API_SECRET", "")
    if not api_key or not api_secret:
        raise EnvironmentError(
            "ALPACA_API_KEY and ALPACA_API_SECRET must be set in .env"
        )
    return StockHistoricalDataClient(api_key, api_secret)


def fetch_bars(
    symbols: List[str],
    start: datetime.date,
    end: datetime.date,
) -> List[Dict]:
    """
    Pull daily OHLCV bars from Alpaca for the given symbols + date range.
    Returns list of dicts: {symbol, date, open, high, low, close, volume, adj_close}.
    """
    from alpaca.data.requests import StockBarsRequest  # type: ignore
    from alpaca.data.timeframe import TimeFrame        # type: ignore

    client = _client()
    request = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame.Day,
        start=datetime.datetime.combine(start, datetime.time.min),
        end=datetime.datetime.combine(end, datetime.time.max),
        feed="iex",
    )
    bars = client.get_stock_bars(request)
    result: List[Dict] = []
    for symbol in symbols:
        if symbol not in bars.data:
            continue
        for bar in bars.data[symbol]:
            result.append({
                "symbol": symbol,
                "date": bar.timestamp.date().isoformat(),
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": int(bar.volume),
                "adj_close": float(bar.close),
            })
    return result


def ingest_daily(
    db_path: str,
    symbols: List[str],
    date: Optional[datetime.date] = None,
) -> List[Dict]:
    """
    Fetch and store EOD bars for the given symbols on `date` (default: today).
    Returns the list of stored records.
    """
    if date is None:
        date = datetime.date.today()
    records = fetch_bars(symbols, start=date, end=date)
    for rec in records:
        store_price(db_path, rec, source=SOURCE)
    return records

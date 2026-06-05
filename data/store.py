"""
Shared price storage — writes to the local SQLite prices table.
Pure I/O: no business logic here.
"""
import datetime
from datetime import timezone
from typing import Dict, List

from db.sqlite import connection


def store_price(db_path: str, record: Dict, source: str = "unknown") -> None:
    """
    Upsert a single OHLCV record into prices.
    record keys: symbol, date, open, high, low, close, volume, adj_close
    """
    now = datetime.datetime.now(timezone.utc).isoformat()
    # Point-in-time stamps (S4): default event_date to the bar date and known_at to now
    # (own EOD pulls become usable on ingest); callers may override for vendor-lagged data.
    event_date = record.get("event_date", record["date"])
    reported_at = record.get("reported_at")
    known_at = record.get("known_at", now)
    with connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO prices
                (symbol, date, open, high, low, close, volume, adj_close, source,
                 event_date, reported_at, ingested_at, known_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date, source) DO UPDATE SET
                open=excluded.open, high=excluded.high, low=excluded.low,
                close=excluded.close, volume=excluded.volume,
                adj_close=excluded.adj_close,
                event_date=excluded.event_date, reported_at=excluded.reported_at,
                ingested_at=excluded.ingested_at, known_at=excluded.known_at
            """,
            (
                record["symbol"],
                record["date"],
                record.get("open"),
                record.get("high"),
                record.get("low"),
                record.get("close"),
                record.get("volume"),
                record.get("adj_close"),
                source,
                event_date,
                reported_at,
                now,
                known_at,
            ),
        )


def get_prices(db_path: str, symbol: str, date: str) -> List[Dict]:
    """Return all price records for a (symbol, date) across all sources."""
    with connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM prices WHERE symbol=? AND date=?", (symbol, date)
        ).fetchall()
    return [dict(r) for r in rows]

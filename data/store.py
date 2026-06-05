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
    with connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO prices
                (symbol, date, open, high, low, close, volume, adj_close, source, ingested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, date, source) DO UPDATE SET
                open=excluded.open, high=excluded.high, low=excluded.low,
                close=excluded.close, volume=excluded.volume,
                adj_close=excluded.adj_close,
                ingested_at=excluded.ingested_at
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
                datetime.datetime.now(timezone.utc).isoformat(),
            ),
        )


def get_prices(db_path: str, symbol: str, date: str) -> List[Dict]:
    """Return all price records for a (symbol, date) across all sources."""
    with connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM prices WHERE symbol=? AND date=?", (symbol, date)
        ).fetchall()
    return [dict(r) for r in rows]

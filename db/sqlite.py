"""
SQLite connection helper — Phase 0.

Schema DDL lives in the per-domain modules (db/market.py, db/sharia.py,
db/portfolio.py, db/learning.py, db/macro.py, db/fundamentals.py, db/news.py),
all created via db.paths.init_all(). This module is ONLY the connection helper —
there is no schema here, so there is no second source of truth for the schema.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional


def utcnow_iso() -> str:
    """The canonical 'now' for the app layer: UTC, ISO-8601, timezone-AWARE. Use this everywhere a row's
    timestamp is set from Python, so every persisted timestamp has the same (tz-aware) shape. The SQLite
    column defaults emit the same shape (strftime ...Z) for rows the app doesn't stamp."""
    return datetime.now(timezone.utc).isoformat()


def parse_ts(s) -> Optional[datetime]:
    """Parse any timestamp this codebase persists into a tz-AWARE UTC datetime, tolerantly: ISO-8601 with
    an offset or 'Z' (the app + new-default format) AND the legacy SQLite `datetime('now')` shape
    ('YYYY-MM-DD HH:MM:SS', naive → assumed UTC). Returns None on junk. This is what makes mixed historical
    timestamp formats safe to compare."""
    if not s:
        return None
    try:
        d = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


@contextmanager
def connection(path: str) -> Iterator[sqlite3.Connection]:
    """
    Open a SQLite connection with a Row factory; commit on success, roll back on
    error, and ALWAYS close. Use:

        with connection(path) as conn:
            conn.execute(...)

    Unlike `with sqlite3.connect(path) as conn:` (which commits but never closes),
    this guarantees the handle is closed — no connection leak over a long-running loop.
    """
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # S6.6: WAL reduces locking under concurrent read/write on the Windows desktop.
    # Persistent per-DB and idempotent; guarded so a filesystem that rejects WAL is non-fatal.
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        # Wait up to 5s for a lock instead of failing instantly — so an overlapping writer (e.g. a manual
        # run-brain during the scheduled one) backs off rather than raising "database is locked".
        conn.execute("PRAGMA busy_timeout=5000")
    except sqlite3.Error:
        pass
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

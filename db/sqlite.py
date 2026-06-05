"""
SQLite connection helper — Phase 0.

Schema DDL lives in the per-domain modules (db/market.py, db/sharia.py,
db/portfolio.py, db/learning.py, db/macro.py, db/fundamentals.py, db/news.py),
all created via db.paths.init_all(). This module is ONLY the connection helper —
there is no schema here, so there is no second source of truth for the schema.
"""
import sqlite3
from contextlib import contextmanager
from typing import Iterator


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
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

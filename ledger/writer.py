"""
Append-only ledger writer with SHA-256 hash chain.

Every entry's hash covers its own fields plus the previous entry's hash,
making any post-hoc tampering detectable during reconciliation.
The agent role has INSERT-only on this table (per db/schema.sql RLS sketch).

Cash-account convention: amounts are signed from the fund's cash perspective —
DEPOSIT and SELL are positive (cash in), BUY is negative (cash out). `balance_after`
is the running cash balance, which is what reconciliation compares against the broker.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from db.sqlite import connection


def _ensure_table(db_path: str) -> None:
    # Canonical schema for `ledger` lives in db/portfolio.py; this defensive
    # CREATE IF NOT EXISTS only lets the writer run before init_all() has been called.
    with connection(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ledger (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                ts           TEXT,
                type         TEXT,
                symbol       TEXT,
                amount       REAL,
                balance_after REAL,
                ref          TEXT,
                hash         TEXT
            )
        """)


def _last_row(conn: sqlite3.Connection) -> Optional[dict]:
    row = conn.execute(
        "SELECT id, ts, type, symbol, amount, balance_after, ref, hash "
        "FROM ledger ORDER BY id DESC LIMIT 1"
    ).fetchone()
    if row is None:
        return None
    keys = ["id", "ts", "type", "symbol", "amount", "balance_after", "ref", "hash"]
    return dict(zip(keys, row))


def _make_hash(ts: str, type_: str, symbol: str, amount: float,
               balance_after: float, ref: str, prev_hash: str) -> str:
    payload = json.dumps({
        "ts": ts, "type": type_, "symbol": symbol,
        "amount": amount, "balance_after": balance_after,
        "ref": ref, "prev_hash": prev_hash,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def append_entry(
    db_path: str,
    type_: str,
    symbol: str,
    amount: float,
    ref: str = "",
) -> int:
    """
    Append one ledger entry and return the new row id.

    `amount` is signed from the cash perspective (DEPOSIT/SELL positive, BUY negative).
    `balance_after` = previous balance + amount (running cash balance). The hash chains
    to the previous row, so any later edit is detectable by verify_hash_chain().
    A failed write propagates the sqlite error (the entry is never silently dropped).
    """
    _ensure_table(db_path)
    now = datetime.now(timezone.utc).isoformat()

    with connection(db_path) as conn:
        last = _last_row(conn)
        prev_balance = last["balance_after"] if last else 0.0
        prev_hash = last["hash"] if last else ""
        balance_after = prev_balance + amount
        h = _make_hash(now, type_, symbol, amount, balance_after, ref, prev_hash)
        cur = conn.execute(
            "INSERT INTO ledger (ts, type, symbol, amount, balance_after, ref, hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (now, type_, symbol, amount, balance_after, ref, h),
        )
        return cur.lastrowid

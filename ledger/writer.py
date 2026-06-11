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
    # Single source of truth for the schema is db/portfolio.py; this defensive ensure just lets the
    # writer run before init_all() has been called on a fresh dir.
    from db.portfolio import init_portfolio_db
    init_portfolio_db(db_path)


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


def _append_on_conn(conn: sqlite3.Connection, now: str, type_: str, symbol: str,
                    amount: float, ref: str) -> int:
    """Append one entry on an existing connection (no commit — the caller owns the transaction)."""
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


def append_entry(
    db_path: str,
    type_: str,
    symbol: str,
    amount: float,
    ref: str = "",
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """
    Append one ledger entry and return the new row id.

    `amount` is signed from the cash perspective (DEPOSIT/SELL positive, BUY negative).
    `balance_after` = previous balance + amount (running cash balance). The hash chains
    to the previous row, so any later edit is detectable by verify_hash_chain().
    A failed write propagates the sqlite error (the entry is never silently dropped).

    **Atomicity (P1-A):** pass an open `conn` to enlist this write in a caller-owned transaction
    (e.g. the broker writing orders + ledger + positions together). When `conn` is given the table
    is assumed to exist and NOTHING is committed here — the outer `connection()` commits or rolls
    back the whole unit. With `conn=None` the behaviour is unchanged (own table-ensure + own commit).
    """
    now = datetime.now(timezone.utc).isoformat()
    if conn is not None:
        return _append_on_conn(conn, now, type_, symbol, amount, ref)
    _ensure_table(db_path)
    with connection(db_path) as own:
        return _append_on_conn(own, now, type_, symbol, amount, ref)

"""
Ledger reconciliation.

Verifies the hash chain for tamper evidence.
Optionally compares the running ledger balance against a broker statement.
For Phase 0 (paper) the "broker balance" can be derived from simulated fills.
"""
from __future__ import annotations
import sqlite3
from dataclasses import dataclass, field
from typing import List, Optional

from ledger.writer import _ensure_table, _make_hash


@dataclass
class ReconcileResult:
    clean: bool
    diffs: List[str] = field(default_factory=list)
    ledger_balance: float = 0.0
    broker_balance: Optional[float] = None


def get_ledger_balance(db_path: str) -> float:
    _ensure_table(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT balance_after FROM ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return row[0] if row else 0.0


def verify_hash_chain(db_path: str) -> List[str]:
    """
    Walk every ledger row and re-compute its hash.
    Returns a list of anomaly descriptions; empty list = chain intact.
    """
    _ensure_table(db_path)
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, ts, type, symbol, amount, balance_after, ref, hash "
            "FROM ledger ORDER BY id"
        ).fetchall()

    anomalies: List[str] = []
    prev_hash = ""
    for row in rows:
        id_, ts, type_, symbol, amount, balance_after, ref, stored = row
        expected = _make_hash(ts, type_, symbol, amount, balance_after, ref, prev_hash)
        if expected != stored:
            anomalies.append(f"Hash mismatch at ledger id={id_}")
        prev_hash = stored
    return anomalies


def reconcile(
    db_path: str,
    broker_balance: Optional[float] = None,
    tolerance: float = 0.01,
) -> ReconcileResult:
    """
    Hash-chain verification + optional balance comparison.
    broker_balance=None → hash-chain check only (Phase 0 default).
    """
    diffs = verify_hash_chain(db_path)
    ledger_bal = get_ledger_balance(db_path)

    if broker_balance is not None:
        diff = abs(ledger_bal - broker_balance)
        if diff > tolerance:
            diffs.append(
                f"Balance mismatch: ledger={ledger_bal:.4f},"
                f" broker={broker_balance:.4f} (Δ={diff:.4f})"
            )

    return ReconcileResult(
        clean=len(diffs) == 0,
        diffs=diffs,
        ledger_balance=ledger_bal,
        broker_balance=broker_balance,
    )

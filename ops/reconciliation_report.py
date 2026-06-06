"""
Full reconciliation report (S6) — ledger vs broker, plus hash-chain integrity.

Wraps ledger.reconcile and adds position context into a single structured report the
dashboard / daily report can surface. Phase 0: broker_balance can be the paper-account cash.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from ledger.reconcile import reconcile


@dataclass
class ReconReport:
    clean: bool
    ledger_balance: float
    broker_balance: Optional[float]
    position_count: int
    diffs: List[str] = field(default_factory=list)


def build_reconciliation(dbs: CamelDbs, broker_balance: Optional[float] = None) -> ReconReport:
    res = reconcile(dbs.portfolio, broker_balance=broker_balance)
    with connection(dbs.portfolio) as conn:
        pos = conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0]
    return ReconReport(
        clean=res.clean, ledger_balance=res.ledger_balance,
        broker_balance=broker_balance, position_count=pos, diffs=list(res.diffs),
    )

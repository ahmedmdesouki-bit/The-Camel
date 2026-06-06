"""
Daily report assembler (S5.5) — console/text first; Telegram delivery in S6.

Pulls the health report (with the GREEN/YELLOW/RED/BLACK status) plus live counts from the
portfolio DB, and renders the founder-facing daily summary.
"""
from __future__ import annotations
from typing import Tuple

from db.paths import CamelDbs
from db.sqlite import connection
from ops.health_monitor import check, daily_report_text


def _counts(dbs: CamelDbs) -> Tuple[int, float]:
    """(open paper positions, paper capital at risk)."""
    with connection(dbs.portfolio) as conn:
        positions = conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0]
        bal = conn.execute(
            "SELECT balance_after FROM ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
    # ledger is a cash account; negative balance after deposits == capital deployed
    paper_at_risk = abs(bal[0]) if bal and bal[0] is not None and bal[0] < 0 else 0.0
    return positions, paper_at_risk


def build_daily_report(dbs: CamelDbs, mode: str = "paper", open_cards: int = 0) -> str:
    report = check(dbs, mode=mode)
    positions, at_risk = _counts(dbs)
    return daily_report_text(report, open_cards=open_cards,
                             open_positions=positions, paper_at_risk=at_risk)

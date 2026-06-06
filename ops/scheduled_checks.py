"""
Scheduled checks (S6) — the weekly safety routine (Windows Task Scheduler fires it).

Runs the kill-switch self-test, a verified backup, and a reconciliation, logs the result to
the operator log, and returns a pass/fail. This is what the roadmap's "weekly kill-switch
test" hangs off.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from db.paths import CamelDbs
from ops.kill_switch_test import run_kill_switch_test
from ops.backup import backup, verify_backup
from ops.reconciliation_report import build_reconciliation
from operator_os.op_log import append as op_append


@dataclass
class WeeklyCheckResult:
    passed: bool
    detail: Dict = field(default_factory=dict)


def run_weekly_checks(dbs: CamelDbs, backup_dir: str) -> WeeklyCheckResult:
    ks = run_kill_switch_test(dbs)
    backup(dbs, backup_dir)
    backup_ok = verify_backup(dbs, backup_dir)
    recon = build_reconciliation(dbs)

    detail = {
        "kill_switch_passed": ks.passed,
        "backup_verified": backup_ok,
        "reconcile_clean": recon.clean,
        "ledger_balance": recon.ledger_balance,
    }
    passed = ks.passed and backup_ok and recon.clean
    op_append(dbs.portfolio, "WEEKLY_CHECK", {**detail, "passed": passed})
    return WeeklyCheckResult(passed=passed, detail=detail)

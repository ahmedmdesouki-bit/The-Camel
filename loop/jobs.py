"""
Scheduled jobs (S10.5, Workstream B) — runnable entrypoints for the built-but-untriggered ops.

Before this, only the daily loop and the manual kill-switch had a `__main__`; the weekly safety job,
the heartbeat/dead-man, the dashboard render, and the founder brief had no scheduled trigger. This
module gives them real entrypoints (mirroring `loop/scheduler.py`) so Windows Task Scheduler can fire:

    python -m loop.jobs daily    # heartbeat + render the dashboard + send the founder brief
    python -m loop.jobs weekly   # kill-switch self-test + backup + reconcile

Each step is best-effort and isolated — one failing step records an error but never aborts the others
or crashes the scheduler. Read-only / paper; nothing here trades.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

from db.paths import CamelDbs


def run_daily_ops(dbs: CamelDbs, *, mode: str = "paper", notifier=None,
                  dashboard_path: Optional[str] = None,
                  price_moves: Optional[Dict[str, float]] = None) -> dict:
    """Beat the heartbeat, render the read-only dashboard, and send the founder daily brief."""
    summary: dict = {"heartbeat": None, "dashboard": None, "brief_sent": None, "errors": {}}

    try:
        from ops.heartbeat import beat
        summary["heartbeat"] = beat(dbs.portfolio)
    except Exception as exc:
        summary["errors"]["heartbeat"] = str(exc)

    try:
        from dashboard.generate import write_dashboard
        if dashboard_path:
            summary["dashboard"] = write_dashboard(dbs, dashboard_path, mode=mode)
    except Exception as exc:
        summary["errors"]["dashboard"] = str(exc)

    try:
        from alerts.brief import send_founder_brief
        r = send_founder_brief(dbs, mode=mode, notifier=notifier, price_moves=price_moves)
        summary["brief_sent"] = r.sent
        summary["brief_preview"] = r.preview
    except Exception as exc:
        summary["errors"]["brief"] = str(exc)

    return summary


def run_weekly_safety(dbs: CamelDbs, backup_dir: str) -> dict:
    """Run the weekly safety routine: kill-switch self-test + backup + reconcile."""
    try:
        from ops.scheduled_checks import run_weekly_checks
        res = run_weekly_checks(dbs, backup_dir)
        return {"ok": True, "result": str(res)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main(argv=None) -> int:                              # pragma: no cover - CLI entrypoint
    import argparse
    p = argparse.ArgumentParser(description="The Camel — scheduled ops jobs")
    p.add_argument("job", choices=["daily", "weekly"])
    p.add_argument("--db-dir", default=os.environ.get("CAMEL_DB_DIR", "."))
    p.add_argument("--dashboard", default=os.environ.get("CAMEL_DASHBOARD_PATH"))
    p.add_argument("--backup-dir", default=os.environ.get("CAMEL_BACKUP_DIR", "./backups"))
    args = p.parse_args(argv)

    dbs = CamelDbs.from_dir(args.db_dir)
    if args.job == "daily":
        print(run_daily_ops(dbs, dashboard_path=args.dashboard))
    else:
        print(run_weekly_safety(dbs, args.backup_dir))
    return 0


if __name__ == "__main__":                               # pragma: no cover
    raise SystemExit(main())

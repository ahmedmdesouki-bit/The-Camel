"""
Machine / operator health monitor (S5; expanded in S5.5/S6; resources + creds wired in the backlog sweep).

Real checks with no *hard* extra dependencies: DB reachability, disk free, kill-switch state, current
mode, guardrail importable, CPU/memory (via psutil if present — gracefully 'n/a' otherwise, never a hard
dep), and broker/Telegram/secrets credential presence (env-based; absent is normal & fine in paper, so it
never degrades the status). Produces a HealthReport and a GREEN/YELLOW/RED/BLACK status classifier (used by
the daily report + Opportunity Router).
"""
from __future__ import annotations
import os
import shutil
from dataclasses import dataclass, field
from typing import Dict, List

from db.sqlite import connection
from db.paths import CamelDbs
from ops.kill_switch import is_halted

# Resource thresholds kept high so the monitor only degrades on genuine pressure (not normal load).
CPU_YELLOW_PCT = 98.0
MEM_YELLOW_PCT = 97.0

# Env vars that, if present, indicate a configured integration. Absence is expected in paper mode.
_BROKER_ENV = ("CAMEL_BROKER_KEY", "ALPACA_API_KEY_ID", "ALPACA_KEY_ID")
_TELEGRAM_ENV = ("CAMEL_TELEGRAM_TOKEN", "TELEGRAM_BOT_TOKEN")
_SECRET_ENV = _BROKER_ENV + _TELEGRAM_ENV + ("FRED_API_KEY", "FINNHUB_API_KEY", "EODHD_API_KEY")


def _resource_checks(checks: Dict[str, str], issues: List[str]) -> None:
    """CPU + memory via psutil if installed; otherwise honestly report 'n/a (psutil absent)'."""
    try:
        import psutil  # optional, never a hard dependency
    except Exception:
        checks["cpu"] = checks["memory"] = "n/a (psutil absent)"
        return
    try:
        cpu = float(psutil.cpu_percent(interval=None))
        mem = float(psutil.virtual_memory().percent)
        checks["cpu"] = f"{cpu:.0f}%"
        checks["memory"] = f"{mem:.0f}%"
        if cpu >= CPU_YELLOW_PCT:
            issues.append(f"high cpu: {cpu:.0f}%")
        if mem >= MEM_YELLOW_PCT:
            issues.append(f"high memory: {mem:.0f}%")
    except Exception as exc:                       # psutil present but query failed — informational
        checks["cpu"] = checks["memory"] = f"unknown ({exc})"


def _cred_checks(checks: Dict[str, str], env: Dict[str, str]) -> None:
    """Credential PRESENCE only (never reads/echoes the value). Absent is fine in paper → no issue."""
    checks["broker"] = "configured" if any(env.get(k) for k in _BROKER_ENV) else "absent (paper)"
    checks["telegram"] = "configured" if any(env.get(k) for k in _TELEGRAM_ENV) else "absent"
    loaded = sum(1 for k in _SECRET_ENV if env.get(k))
    checks["secrets"] = f"{loaded} loaded" if loaded else "none (paper)"


@dataclass
class HealthReport:
    status: str                                   # GREEN | YELLOW | RED | BLACK
    mode: str
    checks: Dict[str, str] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


def _db_ok(path: str) -> bool:
    try:
        with connection(path) as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False


def check(dbs: CamelDbs, mode: str = "paper", min_disk_gb: float = 1.0) -> HealthReport:
    checks: Dict[str, str] = {}
    issues: List[str] = []

    # DB reachability (real)
    db_paths = {"market": dbs.market, "sharia": dbs.sharia,
                "portfolio": dbs.portfolio, "learning": dbs.learning}
    for name, p in db_paths.items():
        ok = _db_ok(p)
        checks[f"db_{name}"] = "ok" if ok else "FAIL"
        if not ok:
            issues.append(f"db {name} unreachable")

    # disk free (real)
    try:
        free_gb = shutil.disk_usage(dbs.portfolio).free / (1024 ** 3)
        checks["disk"] = f"{free_gb:.1f}GB free"
        if free_gb < min_disk_gb:
            issues.append(f"low disk: {free_gb:.1f}GB")
    except Exception as exc:
        checks["disk"] = f"unknown ({exc})"
        issues.append("disk check unknown")   # S6.6: fail-safe — unknown disk degrades to YELLOW

    # kill switch (real)
    halted = is_halted()
    checks["kill_switch"] = "HALTED" if halted else "off"

    # guardrail importable (real)
    try:
        import guardrail.constitution  # noqa: F401
        checks["guardrail"] = "ok"
    except Exception:
        checks["guardrail"] = "FAIL"
        issues.append("guardrail import failed")

    # resources (psutil-optional) + credential presence (env-based)
    _resource_checks(checks, issues)
    _cred_checks(checks, dict(os.environ))

    checks["mode"] = mode

    # ---- status classifier ----
    db_fail = any(v == "FAIL" for k, v in checks.items() if k.startswith("db_"))
    if halted:
        status = "BLACK"            # kill switch / manual intervention required
    elif db_fail or checks.get("guardrail") == "FAIL":
        status = "RED"             # halt all consequential actions
    elif issues:
        status = "YELLOW"          # research only
    else:
        status = "GREEN"
    return HealthReport(status=status, mode=mode, checks=checks, issues=issues)


def daily_report_text(report: HealthReport, open_cards: int = 0, open_positions: int = 0,
                      paper_at_risk: float = 0.0) -> str:
    return (
        "Camel Daily Health Report\n"
        f"System status: {report.status} | Mode: {report.mode} | "
        f"Broker: {report.checks.get('broker','?')} | DB: "
        f"{'Connected' if all(report.checks.get(f'db_{n}')=='ok' for n in ('market','sharia','portfolio','learning')) else 'DEGRADED'}\n"
        f"Guardrail Service: {report.checks.get('guardrail','?')} | "
        f"Open thesis cards: {open_cards} | Open paper positions: {open_positions}\n"
        f"Live capital at risk: $0 | Paper capital at risk: ${paper_at_risk:.0f} | "
        f"Issues: {', '.join(report.issues) or 'None'}"
    )

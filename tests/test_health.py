"""
S5 — health monitor + status classifier.  (S6.6: disk checks mocked for portability.)
"""
from collections import namedtuple
from unittest.mock import patch

from ops.health_monitor import check, daily_report_text
from ops.kill_switch import halt, resume

_Usage = namedtuple("usage", "total used free")


def test_green_when_all_ok(dbs):
    r = check(dbs, mode="paper")
    assert r.status == "GREEN" and r.issues == []
    assert all(r.checks[f"db_{n}"] == "ok" for n in ("market", "sharia", "portfolio", "learning"))

def test_black_when_halted(dbs):
    halt()
    try:
        r = check(dbs, mode="paper")
        assert r.status == "BLACK" and r.checks["kill_switch"] == "HALTED"
    finally:
        resume()

def test_red_when_db_unreachable(dbs):
    dbs.portfolio = "Z:/nonexistent/path/camel_portfolio.db"   # force a DB failure
    r = check(dbs, mode="paper")
    assert r.status == "RED" and any("portfolio" in i for i in r.issues)

@patch("ops.health_monitor.shutil.disk_usage")
def test_yellow_when_low_disk(mock_usage, dbs):
    # S6.6: mock disk so the test is deterministic across environments (no real-disk dependence)
    mock_usage.return_value = _Usage(total=100 * 1024**3, used=99 * 1024**3, free=int(0.5 * 1024**3))
    r = check(dbs, mode="paper", min_disk_gb=1.0)
    assert r.status == "YELLOW" and any("low disk" in i for i in r.issues)

@patch("ops.health_monitor.shutil.disk_usage")
def test_yellow_when_disk_check_unknown(mock_usage, dbs):
    # S6.6: an unknown/errored disk check fails safe to YELLOW, not GREEN
    mock_usage.side_effect = OSError("disk query failed")
    r = check(dbs, mode="paper")
    assert r.status == "YELLOW" and any("unknown" in i for i in r.issues)

def test_daily_report_text_contains_status(dbs):
    r = check(dbs, mode="paper")
    txt = daily_report_text(r, open_cards=3, open_positions=2, paper_at_risk=430)
    assert "Camel Daily Health Report" in txt
    assert f"System status: {r.status}" in txt
    assert "Paper capital at risk: $430" in txt

def test_skipped_checks_present(dbs):
    r = check(dbs, mode="paper")
    for k in ("cpu", "memory", "broker", "telegram", "secrets"):
        assert "skipped" in r.checks[k]

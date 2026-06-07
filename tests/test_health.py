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

def test_resource_and_cred_checks_present(dbs):
    # backlog sweep: cpu/memory/broker/telegram/secrets are now REAL checks (no more 'skipped').
    r = check(dbs, mode="paper")
    for k in ("cpu", "memory", "broker", "telegram", "secrets"):
        assert k in r.checks and "skipped" not in r.checks[k]
    # cpu/memory either report a value or honestly say psutil is absent — never a stub placeholder
    assert "%" in r.checks["cpu"] or "n/a" in r.checks["cpu"] or "unknown" in r.checks["cpu"]


def test_broker_cred_detected_when_env_set(dbs, monkeypatch):
    monkeypatch.setenv("CAMEL_BROKER_KEY", "dummy-not-a-real-key")
    r = check(dbs, mode="paper")
    assert r.checks["broker"] == "configured"
    assert "loaded" in r.checks["secrets"]
    # presence-only: the secret value is never echoed into the report
    assert "dummy-not-a-real-key" not in str(r.checks)


def test_no_broker_cred_is_fine_in_paper(dbs, monkeypatch):
    for k in ("CAMEL_BROKER_KEY", "ALPACA_API_KEY_ID", "ALPACA_KEY_ID"):
        monkeypatch.delenv(k, raising=False)
    r = check(dbs, mode="paper")
    assert r.checks["broker"] == "absent (paper)"
    assert r.status == "GREEN"          # absent creds must NOT degrade status in paper

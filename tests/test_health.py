"""
S5 — health monitor + status classifier.
"""
from ops.health_monitor import check, daily_report_text
from ops.kill_switch import halt, resume


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

def test_yellow_when_low_disk(dbs):
    # demand an absurd amount of free disk so the disk check raises an issue (but DBs ok)
    r = check(dbs, mode="paper", min_disk_gb=10_000_000)
    assert r.status == "YELLOW"

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

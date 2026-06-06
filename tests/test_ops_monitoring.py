"""
S6b — monitoring/ops: heartbeat, log rotation, secrets manager, reconciliation,
off-box archive, weekly scheduled checks, daily-loss-stop simulation.
"""
import os
import pytest

from ops.heartbeat import beat, last_beat, is_alive
from ops.log_rotation import rotate_if_needed
from ops.secrets_manager import enforce_startup, PlaintextSecretError, get_secret
from ops.reconciliation_report import build_reconciliation
from ops.archive import archive_backup, verify_archive
from ops.scheduled_checks import run_weekly_checks
from ledger.writer import append_entry
from capital.allocator import Allocator
from guardrail.constitution import Action, ActionType, Instrument, PortfolioState, Thesis


# ---------------- heartbeat ----------------

def test_heartbeat_beat_and_read(dbs):
    ts = beat(dbs.portfolio, now="2026-06-06T12:00:00+00:00")
    assert last_beat(dbs.portfolio) == ts

def test_heartbeat_single_row(dbs):
    beat(dbs.portfolio, now="2026-06-06T12:00:00+00:00")
    beat(dbs.portfolio, now="2026-06-06T12:05:00+00:00")
    import sqlite3
    with sqlite3.connect(dbs.portfolio) as c:
        assert c.execute("SELECT COUNT(*) FROM heartbeat").fetchone()[0] == 1
    assert last_beat(dbs.portfolio) == "2026-06-06T12:05:00+00:00"

def test_heartbeat_alive_and_stale(dbs):
    beat(dbs.portfolio, now="2026-06-06T12:00:00+00:00")
    assert is_alive(dbs.portfolio, "2026-06-06T12:30:00+00:00", max_age_seconds=3600)
    assert not is_alive(dbs.portfolio, "2026-06-06T14:00:00+00:00", max_age_seconds=3600)

def test_heartbeat_dead_when_never_beat(dbs):
    assert not is_alive(dbs.portfolio, "2026-06-06T12:00:00+00:00")


# ---------------- log rotation ----------------

def test_no_rotation_when_small(tmp_path):
    p = tmp_path / "noah.log"; p.write_text("small")
    assert not rotate_if_needed(str(p), max_bytes=1000)

def test_rotation_when_oversized(tmp_path):
    p = tmp_path / "camel.log"; p.write_text("x" * 2000)
    assert rotate_if_needed(str(p), max_bytes=1000, keep=3)
    assert os.path.exists(str(p)) and os.path.getsize(str(p)) == 0   # fresh empty
    assert os.path.exists(str(p) + ".1")                              # rolled

def test_rotation_keeps_n(tmp_path):
    p = str(tmp_path / "camel.log")
    for _ in range(5):
        open(p, "w").write("x" * 2000)
        rotate_if_needed(p, max_bytes=1000, keep=2)
    assert os.path.exists(p + ".1") and os.path.exists(p + ".2")
    assert not os.path.exists(p + ".3")   # capped at keep=2


# ---------------- secrets manager (hard refusal) ----------------

def test_strict_raises_on_plaintext_secret():
    with pytest.raises(PlaintextSecretError):
        enforce_startup({"ALPACA_API_SECRET": "AK1realsecretvalue123456"}, strict=True)

def test_strict_passes_on_placeholders():
    assert enforce_startup({"ALPACA_API_KEY": "your_paper_key"}, strict=True) == []

def test_warn_only_returns_offenders():
    # a non-placeholder value (not shaped like a real key, to avoid the secrets-leak scanner)
    offenders = enforce_startup({"OPENAI_API_KEY": "redacted-openai-keyvalue"}, strict=False)
    assert "OPENAI_API_KEY" in offenders

def test_get_secret_env_fallback(monkeypatch):
    monkeypatch.setenv("SOME_KEY", "value123")
    assert get_secret("SOME_KEY") == "value123"


# ---------------- reconciliation report ----------------

def test_reconciliation_clean(dbs):
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    r = build_reconciliation(dbs, broker_balance=1000.0)
    assert r.clean and r.ledger_balance == pytest.approx(1000.0) and r.position_count == 0

def test_reconciliation_balance_mismatch(dbs):
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    r = build_reconciliation(dbs, broker_balance=900.0)
    assert not r.clean and any("mismatch" in d.lower() for d in r.diffs)


# ---------------- off-box archive ----------------

def test_archive_and_verify(dbs, tmp_path):
    append_entry(dbs.portfolio, "DEPOSIT", "", 500.0)
    z = str(tmp_path / "camel_backup.zip")
    archive_backup(dbs, z)
    assert os.path.exists(z) and verify_archive(dbs, z)

def test_verify_archive_false_for_missing(dbs, tmp_path):
    assert not verify_archive(dbs, str(tmp_path / "nope.zip"))


# ---------------- weekly scheduled checks ----------------

def test_weekly_checks_pass(dbs, tmp_path):
    result = run_weekly_checks(dbs, str(tmp_path / "wk"))
    assert result.passed
    assert result.detail["kill_switch_passed"] and result.detail["backup_verified"]
    # it logged to the op log
    import sqlite3
    with sqlite3.connect(dbs.portfolio) as c:
        n = c.execute("SELECT COUNT(*) FROM op_log WHERE event_type='WEEKLY_CHECK'").fetchone()[0]
    assert n == 1


# ---------------- daily-loss-stop simulation (S6 gate) ----------------

def _state(**kw):
    wl = {"SPUS": Instrument("SPUS", "Diversified", "compliant", on_whitelist=True)}
    s = PortfolioState(fund_usd=10_000, cash_usd=5_000, whitelist=wl)
    for k, v in kw.items():
        setattr(s, k, v)
    return s

def _buy():
    return Action(type=ActionType.TRADE, symbol="SPUS", side="buy", notional_usd=500,
                  instrument_type="etf", thesis=Thesis("x", "y", "z"), mode="paper")

def test_daily_loss_stop_simulation_halts_trading():
    # simulate a -6% day → the allocator must reject via the Constitution circuit breaker
    r = Allocator().request(_buy(), _state(day_pnl_pct=-0.06))
    assert not r.approved and r.decision.limit_hit == "daily_loss_stop"

"""
S5.5 — Minimal Ops Visibility: secrets check, backup/restore, kill-switch self-test, daily report.
"""
import os
import sqlite3
import pytest

from ops.secrets_check import check_startup, scan_plaintext_env, is_placeholder
from ops.backup import backup, verify_backup, restore
from ops.kill_switch_test import run_kill_switch_test
from ops.daily_report import build_daily_report
from data.store import store_price
from ledger.writer import append_entry


# ---------------- secrets check ----------------

def test_placeholder_env_is_clean():
    env = {"ALPACA_API_KEY": "your_paper_key", "ALPACA_API_SECRET": "", "ALPACA_PAPER": "true"}
    r = check_startup(env)
    assert r.clean and r.plaintext_keys == []

def test_real_secret_flagged():
    env = {"ALPACA_API_SECRET": "AK1A9ZxQ12realsecretvalue9876"}
    r = check_startup(env)
    assert not r.clean and "ALPACA_API_SECRET" in r.plaintext_keys
    assert r.warnings and "secrets manager" in r.warnings[0].lower() or "credential" in r.warnings[0].lower()

def test_is_placeholder():
    assert is_placeholder("") and is_placeholder("your_paper_key") and is_placeholder("true")
    assert not is_placeholder("AK1A9ZxQ12realsecretvalue")

def test_scan_only_named_keys():
    env = {"RANDOM_VAR": "looks-real-but-not-sensitive-123456"}
    assert scan_plaintext_env(env) == []


# ---------------- backup / restore ----------------

def test_backup_and_verify(dbs, tmp_path):
    store_price(dbs.market, dict(symbol="SPUS", date="2026-06-05", open=1, high=1,
                                 low=1, close=50, volume=1, adj_close=50), source="alpaca")
    dest = str(tmp_path / "backup")
    hashes = backup(dbs, dest)
    assert "market" in hashes and "portfolio" in hashes
    assert verify_backup(dbs, dest)

def test_verify_fails_after_source_changes(dbs, tmp_path):
    dest = str(tmp_path / "backup")
    backup(dbs, dest)
    # mutate a source DB after the backup → verify must fail
    store_price(dbs.market, dict(symbol="HLAL", date="2026-06-05", open=1, high=1,
                                 low=1, close=30, volume=1, adj_close=30), source="alpaca")
    assert not verify_backup(dbs, dest)

def test_restore_round_trip(dbs, tmp_path):
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    dest = str(tmp_path / "backup")
    backup(dbs, dest)
    # corrupt the live ledger, then restore
    append_entry(dbs.portfolio, "BUY", "SPUS", -300.0)
    restore(dbs, dest)
    with sqlite3.connect(dbs.portfolio) as conn:
        n = conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
    assert n == 1  # restored to the single DEPOSIT row


# ---------------- kill-switch self-test ----------------

def test_kill_switch_self_test_passes(dbs):
    result = run_kill_switch_test(dbs)
    assert result.passed
    assert result.detail["halted_outcome"] == "halted"
    assert result.detail["resumed_outcome"] == "complete"


# ---------------- daily report ----------------

def test_daily_report_renders_status(dbs):
    txt = build_daily_report(dbs, mode="paper")
    assert "Noah Daily Health Report" in txt
    assert "System status: GREEN" in txt          # fresh empty DBs, kill switch off
    assert "Open paper positions: 0" in txt

def test_daily_report_capital_at_risk(dbs):
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    append_entry(dbs.portfolio, "BUY", "SPUS", -300.0)   # net cash 700, deployed 300
    txt = build_daily_report(dbs, mode="paper")
    # balance_after is +700 (still positive cash) → not "at risk" by our negative-balance rule
    assert "Paper capital at risk: $0" in txt

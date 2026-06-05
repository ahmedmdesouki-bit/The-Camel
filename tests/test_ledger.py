"""
Sprint 3 — Ledger + reconciliation tests.  DB: dbs.portfolio (noah_portfolio.db).
"""
import pytest
import sqlite3
from ledger.writer import append_entry
from ledger.reconcile import get_ledger_balance, verify_hash_chain, reconcile


@pytest.fixture
def tmp_db(dbs):
    return dbs.portfolio


# ─────────────────── basic append ───────────────────────────────

def test_single_entry_lands(tmp_db):
    assert append_entry(tmp_db, "DEPOSIT", "", 1000.0, ref="seed") == 1
    assert get_ledger_balance(tmp_db) == pytest.approx(1000.0)

def test_running_balance_accumulates(tmp_db):
    append_entry(tmp_db, "DEPOSIT", "", 1000.0)
    append_entry(tmp_db, "BUY", "SPUS", -300.0, ref="order_1")
    append_entry(tmp_db, "BUY", "HLAL", -200.0, ref="order_2")
    assert get_ledger_balance(tmp_db) == pytest.approx(500.0)

def test_balance_zero_on_empty(tmp_db):
    assert get_ledger_balance(tmp_db) == 0.0

def test_multiple_entries_sequential_ids(tmp_db):
    id1 = append_entry(tmp_db, "DEPOSIT", "", 500.0)
    id2 = append_entry(tmp_db, "BUY", "SPUS", -100.0)
    assert id2 == id1 + 1


# ─────────────────── hash chain ─────────────────────────────────

def test_hash_chain_valid_after_entries(tmp_db):
    append_entry(tmp_db, "DEPOSIT", "", 1000.0)
    append_entry(tmp_db, "BUY", "SPUS", -300.0)
    append_entry(tmp_db, "SELL", "SPUS", 350.0)
    assert verify_hash_chain(tmp_db) == []

def test_hash_chain_empty_ledger(tmp_db):
    assert verify_hash_chain(tmp_db) == []

def test_hash_chain_tamper_detected(tmp_db):
    append_entry(tmp_db, "DEPOSIT", "", 1000.0)
    append_entry(tmp_db, "BUY", "SPUS", -300.0)
    with sqlite3.connect(tmp_db) as conn:
        conn.execute("UPDATE ledger SET amount=-9999 WHERE id=2")
    anomalies = verify_hash_chain(tmp_db)
    assert len(anomalies) >= 1 and "mismatch" in anomalies[0].lower()


# ─────────────────── reconcile ──────────────────────────────────

def test_reconcile_clean_hash_only(tmp_db):
    append_entry(tmp_db, "DEPOSIT", "", 1000.0)
    result = reconcile(tmp_db)
    assert result.clean and result.diffs == []

def test_reconcile_balance_match(tmp_db):
    append_entry(tmp_db, "DEPOSIT", "", 500.0)
    append_entry(tmp_db, "BUY", "SPUS", -200.0)
    result = reconcile(tmp_db, broker_balance=300.0)
    assert result.clean and result.ledger_balance == pytest.approx(300.0)

def test_reconcile_balance_mismatch(tmp_db):
    append_entry(tmp_db, "DEPOSIT", "", 1000.0)
    result = reconcile(tmp_db, broker_balance=900.0)
    assert not result.clean and any("mismatch" in d.lower() for d in result.diffs)

def test_reconcile_tamper_makes_dirty(tmp_db):
    append_entry(tmp_db, "DEPOSIT", "", 1000.0)
    with sqlite3.connect(tmp_db) as conn:
        conn.execute("UPDATE ledger SET amount=9999 WHERE id=1")
    assert not reconcile(tmp_db).clean

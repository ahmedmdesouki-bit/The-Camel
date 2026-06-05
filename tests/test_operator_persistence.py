"""
S5 — task queue, learning ledger, op log.
"""
import pytest
from operator_os import task_queue, learning_ledger, op_log


# ---------------- task queue ----------------

def test_enqueue_and_list_pending(dbs):
    t1 = task_queue.enqueue(dbs.portfolio, "OBSERVE", {"market": "US"})
    t2 = task_queue.enqueue(dbs.portfolio, "RESEARCH", {"symbol": "SPUS"})
    pend = task_queue.list_pending(dbs.portfolio)
    assert [t["id"] for t in pend] == [t1, t2]

def test_next_task_is_fifo(dbs):
    task_queue.enqueue(dbs.portfolio, "A")
    task_queue.enqueue(dbs.portfolio, "B")
    assert task_queue.next_task(dbs.portfolio)["task_type"] == "A"

def test_set_status_removes_from_pending(dbs):
    tid = task_queue.enqueue(dbs.portfolio, "A")
    task_queue.set_status(dbs.portfolio, tid, "done")
    assert task_queue.list_pending(dbs.portfolio) == []
    assert task_queue.get_task(dbs.portfolio, tid)["status"] == "done"

def test_invalid_status_rejected(dbs):
    tid = task_queue.enqueue(dbs.portfolio, "A")
    with pytest.raises(ValueError):
        task_queue.set_status(dbs.portfolio, tid, "bogus")

def test_next_task_none_when_empty(dbs):
    assert task_queue.next_task(dbs.portfolio) is None


# ---------------- learning ledger ----------------

def test_record_decision_and_outcome(dbs):
    eid = learning_ledger.record_decision(
        dbs.learning, "TRADE", "SPUS dip buy", expected_outcome="+5% in 1m", ref="order_1")
    learning_ledger.record_outcome(
        dbs.learning, eid, actual_outcome="+3%", mistake_type="OK",
        lesson_learned="entry timing fine; size could be larger")
    entry = learning_ledger.get_entry(dbs.learning, eid)
    assert entry["decision_type"] == "TRADE"
    assert entry["actual_outcome"] == "+3%"
    assert "timing" in entry["lesson_learned"]

def test_list_lessons_only_resolved(dbs):
    a = learning_ledger.record_decision(dbs.learning, "TRADE", "a")
    learning_ledger.record_decision(dbs.learning, "TRADE", "b")   # no outcome/lesson
    learning_ledger.record_outcome(dbs.learning, a, "win", lesson_learned="buy the dip")
    lessons = learning_ledger.list_lessons(dbs.learning)
    assert len(lessons) == 1 and lessons[0]["lesson_learned"] == "buy the dip"

def test_shared_across_arms(dbs):
    learning_ledger.record_decision(dbs.learning, "TRADE", "t")
    learning_ledger.record_decision(dbs.learning, "PRODUCT", "p")
    # both arms write to the same ledger
    import sqlite3
    with sqlite3.connect(dbs.learning) as conn:
        types = {r[0] for r in conn.execute("SELECT decision_type FROM learning_ledger")}
    assert {"TRADE", "PRODUCT"} <= types


# ---------------- op log ----------------

def test_op_log_append_and_tail(dbs):
    op_log.append(dbs.portfolio, "STATE_TRANSITION", {"from": "IDLE", "to": "OBSERVING"})
    op_log.append(dbs.portfolio, "ROUTER", "chose wait")
    rows = op_log.tail(dbs.portfolio, n=10)
    assert len(rows) == 2
    assert rows[0]["event_type"] == "ROUTER"   # newest first

def test_op_log_string_detail(dbs):
    op_log.append(dbs.portfolio, "TOOL_CALL", "github commit")
    assert op_log.tail(dbs.portfolio)[0]["detail"] == "github commit"

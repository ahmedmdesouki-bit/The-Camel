"""
S17.7 — the Kitchen (watch + control), brain side.

Watch: the desk status + Opportunity Board ride the existing `system_state` snapshot (no new display
tables). Control: the founder-only command channel gains pause/resume/run-desk + approve/veto/prioritize —
the web only REQUESTS, the brain validates and acts. Every control is founder-only + fail-closed, and none
of them moves money.
"""
from db.sqlite import connection
from sharia.whitelist import add_instrument
from ops import command_poller
from governance.desk_control import is_paused, set_paused
from research.workforce import default_workforce
from loop.opportunity_board import build_board, current_board
from dashboard.snapshot import build_snapshot


def _cmd(ctype, payload, by="chiko@x.com"):
    return {"type": ctype, "payload": payload, "requested_by": by}


def _founder():
    return {"founder_email": "chiko@x.com"}


# ================= watch: the snapshot carries desks + board =================

def test_snapshot_carries_desks_and_board(dbs):
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    default_workforce().run_desk(dbs, "steward")
    build_board(dbs, symbols=["SPUS"], edge_fn=lambda d, s: None)   # no edge → a dca row
    snap = build_snapshot(dbs)
    assert "desks" in snap and "board" in snap
    assert any(d["desk_id"] == "steward" for d in snap["desks"])
    assert snap["board"] and snap["board"][0]["symbol"] == "SPUS"
    assert "reason_chain" in snap["board"][0]


# ================= control: founder-only + fail-closed =================

def test_kitchen_controls_are_founder_only(dbs):
    # no founder configured → disabled
    r = command_poller.process_command(dbs, _cmd("pause_desk", {"desk": "quant"}), founder_email="")
    assert not r["ok"] and "CAMEL_FOUNDER_EMAIL" in r["error"]
    # a non-founder requester → refused
    r = command_poller.process_command(
        dbs, _cmd("pause_desk", {"desk": "quant"}, by="friend@x.com"), **_founder())
    assert not r["ok"] and "founder-only" in r["error"]
    assert not is_paused(dbs, "quant")              # nothing changed


def test_pause_and_resume_a_desk(dbs):
    r = command_poller.process_command(dbs, _cmd("pause_desk", {"desk": "quant"}), **_founder())
    assert r["ok"] and r["paused"] and is_paused(dbs, "quant")
    # a paused desk runs nothing
    res = default_workforce().run_desk(dbs, "quant")
    assert res.status == "paused"
    with connection(dbs.learning) as conn:
        assert conn.execute("SELECT COUNT(*) FROM desk_runs WHERE desk_id='quant' AND status='paused'"
                            ).fetchone()[0] >= 1
    r = command_poller.process_command(dbs, _cmd("resume_desk", {"desk": "quant"}), **_founder())
    assert r["ok"] and not r["paused"] and not is_paused(dbs, "quant")


def test_run_desk_now(dbs):
    from ledger.writer import append_entry
    append_entry(dbs.portfolio, "DEPOSIT", "", 500.0)
    r = command_poller.process_command(dbs, _cmd("run_desk", {"desk": "steward"}), **_founder())
    assert r["ok"] and r["desk"] == "steward" and r["status"] == "ok"


def test_approve_and_veto_a_proposal(dbs):
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    build_board(dbs, symbols=["SPUS"], edge_fn=lambda d, s: None)
    pid = current_board(dbs)[0]["id"]
    r = command_poller.process_command(dbs, _cmd("approve_proposal", {"id": pid}), **_founder())
    assert r["ok"] and r["decision"] == "approved"
    with connection(dbs.learning) as conn:
        row = conn.execute("SELECT status, decided_by FROM opportunity_proposals WHERE id=?", (pid,)).fetchone()
    assert row["status"] == "approved" and row["decided_by"] == "chiko@x.com"
    # approving does NOT move money — it records intent; execution still runs through the governed tick
    with connection(dbs.portfolio) as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0


def test_prioritize_reorders_the_board(dbs):
    for s in ("AAA", "BBB"):
        add_instrument(dbs.sharia, s, "etf", approved_by="founder", scan_id="t")
    # both get a dca row (no edge); AAA happens to sort first by id
    build_board(dbs, symbols=["AAA", "BBB"], edge_fn=lambda d, s: None)
    board = current_board(dbs)
    bbb_id = next(r["id"] for r in board if r["symbol"] == "BBB")
    r = command_poller.process_command(dbs, _cmd("prioritize_proposal", {"id": bbb_id, "rank": 99}), **_founder())
    assert r["ok"]
    assert current_board(dbs)[0]["symbol"] == "BBB"      # founder pinned it to the top


def test_missing_args_are_clean_errors(dbs):
    assert not command_poller.process_command(dbs, _cmd("pause_desk", {}), **_founder())["ok"]
    assert not command_poller.process_command(dbs, _cmd("approve_proposal", {}), **_founder())["ok"]

"""
S17.5 — memory consolidation: desk-reliability rollup + pattern detection + persistence.
"""
from db.sqlite import connection
from research.workforce import record_desk_run, DeskResult
from research.memory import consolidate, detect_patterns


def test_consolidate_desk_reliability(dbs):
    record_desk_run(dbs, DeskResult("scout", "ok"))
    record_desk_run(dbs, DeskResult("scout", "ok"))
    record_desk_run(dbs, DeskResult("scout", "error", error="boom"))
    record_desk_run(dbs, DeskResult("scout", "error", error="boom2"))
    record_desk_run(dbs, DeskResult("oracle", "ok"))
    m = consolidate(dbs, persist=False)
    scout = m["desks"]["scout"]
    assert scout["runs"] == 4 and scout["errors"] == 2 and scout["error_rate"] == 0.5
    assert any(p["kind"] == "unreliable_desk" and p["subject"] == "scout" for p in m["patterns"])
    assert "oracle" in m["desks"]
    assert not any(p["subject"] == "oracle" for p in m["patterns"])     # 1 ok run -> too little to judge


def test_consolidate_persists_a_row(dbs):
    consolidate(dbs, persist=True)
    with connection(dbs.learning) as conn:
        n = conn.execute("SELECT COUNT(*) FROM memory_consolidation").fetchone()[0]
    assert n == 1


def test_detect_patterns_pure():
    desks = {"flaky": {"runs": 5, "error_rate": 0.6}, "solid": {"runs": 5, "error_rate": 0.0}}
    strategies = {"weak": {"base_rate": 0.40, "n": 30}, "good": {"base_rate": 0.55, "n": 30}}
    kinds = {(p["kind"], p["subject"]) for p in detect_patterns(desks, strategies)}
    assert ("unreliable_desk", "flaky") in kinds
    assert ("underperforming_strategy", "weak") in kinds
    assert ("unreliable_desk", "solid") not in kinds
    assert ("underperforming_strategy", "good") not in kinds

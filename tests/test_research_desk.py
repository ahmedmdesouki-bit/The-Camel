"""
S12.5 — Research Desk: evidence-object contract, the master switch (DORMANT by default), the token
budget, and the hard rule that a desk can only WRITE EVIDENCE, never act.
"""
from db.sqlite import connection
from sharia.whitelist import add_instrument
from research.evidence import EvidenceObject
from research.desk import ResearchDesk, write_evidence, AnalystDesk
from research.desks import ShariaDesk, MacroDesk


def _count_evidence(dbs):
    with connection(dbs.learning) as conn:
        return conn.execute("SELECT COUNT(*) FROM research_evidence").fetchone()[0]


# ---------------- contract ----------------

def test_evidence_object_validation():
    ok = EvidenceObject(desk="d", claim="x", scope="AAPL", source_count=2, confidence=0.7, direction="positive")
    assert ok.valid()
    assert not EvidenceObject(desk="d", claim="", scope="AAPL", source_count=2).valid()       # no claim
    assert not EvidenceObject(desk="d", claim="x", scope="AAPL", source_count=0).valid()       # no source
    assert not EvidenceObject(desk="d", claim="x", scope="AAPL", source_count=1, confidence=2).valid()
    assert not EvidenceObject(desk="d", claim="x", scope="AAPL", source_count=1, direction="up").valid()


def test_write_evidence_refuses_invalid(dbs):
    assert write_evidence(dbs, EvidenceObject(desk="d", claim="", scope="", source_count=0)) is None
    assert _count_evidence(dbs) == 0


# ---------------- master switch (dormant by default) ----------------

def test_master_switch_defaults_off(dbs):
    add_instrument(dbs.sharia, "AAPL", "stock", approved_by="x", scan_id="s1")
    rd = ResearchDesk()                          # enabled defaults to False
    rd.register(ShariaDesk()); rd.register(MacroDesk())
    assert rd.run(dbs) == [] and _count_evidence(dbs) == 0   # dormant: nothing runs, nothing written


def test_enabled_desk_writes_evidence(dbs):
    with connection(dbs.sharia) as conn:
        conn.execute("INSERT INTO sharia_status (symbol, final_status, drift, confidence) "
                     "VALUES ('SCHD','frozen',1,0.9)")
    rd = ResearchDesk(enabled=True, token_budget=5)
    rd.register(ShariaDesk())
    ev = rd.run(dbs)
    assert len(ev) == 1 and ev[0].direction == "negative" and "SCHD" in ev[0].claim
    assert _count_evidence(dbs) == 1             # persisted to research_evidence


def test_token_budget_caps_desks(dbs):
    with connection(dbs.sharia) as conn:
        conn.execute("INSERT INTO sharia_status (symbol, final_status, drift, confidence) VALUES ('SCHD','frozen',1,0.9)")
    with connection(dbs.macro) as conn:
        conn.execute("INSERT INTO regime_history (classified_at, regime, confidence) VALUES ('2026-06-07','RECESSION_RISK',0.7)")
    rd = ResearchDesk(enabled=True, token_budget=1)   # only enough for ONE desk
    rd.register(ShariaDesk()); rd.register(MacroDesk())
    rd.run(dbs)
    assert _count_evidence(dbs) == 1                  # budget stopped the second desk


# ---------------- the hard rule: evidence only, never act ----------------

def test_desk_has_no_execute_path():
    desk = ShariaDesk()
    for forbidden in ("act", "execute", "trade", "place_order", "buy", "sell"):
        assert not hasattr(desk, forbidden)          # a desk literally cannot act
    assert hasattr(desk, "analyze")                  # it can only analyze → evidence

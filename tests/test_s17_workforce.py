"""
S17.1 — the desk framework + 7-desk roster.

Covers: the no-act invariant (evidence desks cannot move money — the trust-inversion), per-desk DeskResults,
SCOUT writes ONLY data tables, run-isolation (a crashing desk is captured not raised), and the desk_runs audit.
"""
from db.sqlite import connection
from ledger.writer import append_entry
from data.store import store_price
from sharia.whitelist import add_instrument
from research.evidence import EvidenceObject
from research.workforce import (
    Workforce, EvidenceDesk, OperatorDesk, DeskResult, default_workforce,
    latest_desk_status, FORBIDDEN_ACT_ATTRS,
)
from research.roster import (
    ScoutDesk, HeraldDesk, OracleDesk, MuftiDesk, QuantDesk, StewardDesk, ConductorDesk,
)


def _stooq_csv(_url):
    return ("Date,Open,High,Low,Close,Volume\n"
            "2026-01-02,10,11,9,10.5,1000\n2026-01-03,10.5,12,10,11.0,1200\n")


# ================= the trust-inversion: evidence desks cannot act =================

def test_evidence_desks_have_no_act_path():
    """The load-bearing guarantee: no evidence desk exposes any execute/trade/act method — there is no
    code path by which an analyst desk could move money."""
    for desk in (HeraldDesk(), OracleDesk(), MuftiDesk(), QuantDesk()):
        assert desk.kind == "evidence"
        assert isinstance(desk, EvidenceDesk)
        for attr in FORBIDDEN_ACT_ATTRS:
            assert not hasattr(desk, attr), f"{desk.desk_id} must not expose .{attr}"


def test_evidence_objects_are_proposals_only():
    ev = EvidenceObject(desk="quant", claim="x", scope="AAPL", source_count=2, confidence=0.6,
                        direction="positive", recommended_action="propose buy")
    assert ev.valid() and isinstance(ev.recommended_action, str)   # a string proposal, not an action


# ================= roster shape + audit =================

def test_default_workforce_has_seven_named_desks():
    wf = default_workforce()
    assert wf.desk_ids() == ["scout", "herald", "oracle", "mufti", "quant", "steward", "conductor"]


def test_run_desk_writes_an_audit_row(dbs):
    wf = default_workforce()
    r = wf.run_desk(dbs, "steward")
    assert r.desk_id == "steward" and r.started_at and r.ended_at
    with connection(dbs.learning) as conn:
        row = conn.execute("SELECT desk_id, status FROM desk_runs ORDER BY id DESC LIMIT 1").fetchone()
    assert row["desk_id"] == "steward"
    assert latest_desk_status(dbs)["steward"]["status"] == r.status


def test_run_isolation_captures_a_crash_not_raises(dbs):
    class _Boom(OperatorDesk):
        desk_id = "boom"
        def run(self, dbs, ctx=None):
            raise RuntimeError("desk exploded")
    wf = Workforce().register(_Boom())
    r = wf.run_desk(dbs, "boom")                              # must NOT raise
    assert r.status == "error" and "exploded" in r.error
    with connection(dbs.learning) as conn:
        assert conn.execute("SELECT COUNT(*) FROM desk_runs WHERE status='error'").fetchone()[0] == 1


def test_unknown_desk_is_a_clean_error(dbs):
    assert default_workforce().run_desk(dbs, "nope").status == "error"


# ================= SCOUT writes ONLY data =================

def test_scout_ingests_prices_and_touches_no_books(dbs):
    r = ScoutDesk().run(dbs, {"symbols": ["SPUS"], "transport": _stooq_csv})
    assert r.status == "ok" and r.metrics["stored"] >= 1
    with connection(dbs.market) as conn:
        assert conn.execute("SELECT COUNT(*) FROM prices WHERE symbol='SPUS'").fetchone()[0] >= 1
    # the portfolio books are untouched — SCOUT cannot place an order or write the ledger
    with connection(dbs.portfolio) as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0] == 0


# ================= evidence desks produce evidence from real DB state =================

def test_mufti_flags_a_non_compliant_name(dbs):
    with connection(dbs.sharia) as conn:                     # a failed Sharia screen on record
        conn.execute("CREATE TABLE IF NOT EXISTS sharia_status (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     " symbol TEXT, final_status TEXT, drift INTEGER, confidence REAL)")
        conn.execute("INSERT INTO sharia_status (symbol, final_status, drift, confidence) VALUES (?,?,?,?)",
                     ("HACK", "fail", 0, 0.95))
    r = MuftiDesk().run(dbs)
    assert r.status == "ok" and any(e.scope == "HACK" and e.direction == "negative" for e in r.evidence)
    with connection(dbs.learning) as conn:                   # evidence was persisted to research_evidence
        assert conn.execute("SELECT COUNT(*) FROM research_evidence WHERE desk='mufti'").fetchone()[0] >= 1


def test_oracle_reports_the_regime(dbs):
    with connection(dbs.macro) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS regime_history (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     " regime TEXT, confidence REAL, classified_at TEXT)")
        conn.execute("INSERT INTO regime_history (regime, confidence, classified_at) VALUES (?,?,?)",
                     ("RECESSION_RISK", 0.7, "2026-01-02"))
    r = OracleDesk().run(dbs)
    assert r.status == "ok" and r.evidence[0].desk == "oracle" and "RECESSION_RISK" in r.evidence[0].claim


def test_herald_surfaces_notable_safe_news(dbs):
    with connection(dbs.news) as conn:
        conn.execute("INSERT INTO news_events (event_id, title, severity, direction, confidence, "
                     "affected_assets, safe) VALUES (?,?,?,?,?,?,1)",
                     ("e1", "Big selloff in tech", 4, "negative", 0.7, '["AAPL"]'))
        conn.execute("INSERT INTO news_events (event_id, title, severity, direction, confidence, "
                     "affected_assets, safe) VALUES (?,?,?,?,?,?,0)",
                     ("e2", "INJECTION redacted", 5, "negative", 0.9, '[]'))   # unsafe → excluded
    r = HeraldDesk().run(dbs)
    assert r.status == "ok" and len(r.evidence) == 1 and r.evidence[0].scope == "AAPL"


def test_quant_emits_an_edge_verdict_per_name(dbs):
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    for i, c in enumerate([10.0 + i * 0.1 for i in range(60)]):
        store_price(dbs.market, {"symbol": "SPUS", "date": f"2025-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}x{i}",
                                 "open": c, "high": c, "low": c, "close": c, "volume": 1000, "adj_close": c})
    r = QuantDesk().run(dbs, {"symbols": ["SPUS"]})
    assert r.status == "ok" and r.evidence[0].scope == "SPUS"
    assert "edge" in r.evidence[0].claim.lower()
    assert r.evidence[0].recommended_action in ("propose buy (edge proven)", "no edge → DCA core")


def test_steward_summarizes_the_book(dbs):
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    r = StewardDesk().run(dbs)
    assert r.status == "ok" and r.metrics["fund"] == 1000.0 and r.metrics["cash"] == 1000.0


def test_conductor_reports_available_evidence_but_builds_no_proposal(dbs):
    # CONDUCTOR is the only buy path, but in S17.1 it assembles nothing — just reports readiness.
    MuftiDesk().run(dbs)                                      # (no evidence on an empty book → fine)
    r = ConductorDesk().run(dbs)
    assert r.status == "ok" and "evidence_available" in r.metrics

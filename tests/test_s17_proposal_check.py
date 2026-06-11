"""
S17.4 — proposal self-check: the coherence invariant for the Opportunity Board.
"""
from types import SimpleNamespace as NS

from loop.proposal_check import check_proposal, audit_board


def _p(**kw):
    d = dict(symbol="X", action="dca", score=1.0, regime="RECOVERY", sharia_status="compliant",
             edge_allowed=False, hit_rate=0.0, sample_size=0, confidence=0.3,
             recommended_action="...", invalidation="edge decays / Sharia drift",
             reason_chain=["Sharia: compliant"])
    d.update(kw)
    return NS(**d)


def test_coherent_buy_passes():
    assert check_proposal(_p(action="buy", edge_allowed=True, hit_rate=0.6, sample_size=80,
                             confidence=0.6)).ok


def test_coherent_dca_passes():
    assert check_proposal(_p(action="dca")).ok


def test_buy_without_edge_is_critical():
    r = check_proposal(_p(action="buy", edge_allowed=False))
    assert not r.ok and any(i.code == "buy_without_edge" for i in r.critical)


def test_noncompliant_accumulation_is_critical():
    r = check_proposal(_p(action="dca", sharia_status="frozen"))
    assert not r.ok and any(i.code == "noncompliant_accumulation" for i in r.critical)


def test_edge_claim_without_evidence_is_critical():
    r = check_proposal(_p(action="buy", edge_allowed=True, hit_rate=0.0, sample_size=0))
    assert not r.ok and any(i.code == "edge_without_evidence" for i in r.critical)


def test_confidence_out_of_range_is_critical():
    assert not check_proposal(_p(confidence=1.5)).ok
    assert not check_proposal(_p(confidence=-0.1)).ok


def test_avoid_compliant_is_warn_only():
    r = check_proposal(_p(action="avoid", sharia_status="compliant"))
    assert r.ok and any(i.severity == "warn" for i in r.issues)


def test_audit_board_flags_only_incoherent():
    board = [_p(symbol="GOOD", action="dca"),
             _p(symbol="BAD", action="buy", edge_allowed=False)]
    a = audit_board(board)
    assert a["checked"] == 2 and a["incoherent"] == ["BAD"]


def test_real_built_board_is_always_coherent(dbs):
    """Invariant: a board built by build_board never contains a CRITICAL incoherence."""
    from loop.opportunity_board import build_board
    from sharia.whitelist import add_instrument
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    add_instrument(dbs.sharia, "HLAL", "etf", approved_by="founder", scan_id="t")

    def edge_fn(_dbs, sym):
        if sym == "SPUS":
            return NS(trade_allowed=True, hit_rate=0.65, sample_size=80, reason="edge confirmed")
        return NS(trade_allowed=False, hit_rate=0.0, sample_size=0, reason="no edge -> DCA")

    board = build_board(dbs, symbols=["SPUS", "HLAL"], edge_fn=edge_fn, persist=False)
    assert audit_board(board)["incoherent"] == []

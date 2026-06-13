"""
S21 — the SKEPTIC: structured, mandatory dissent. A buy is never a clean concur; thin-sample or
into-risk-off alpha is opposed; a non-compliant accumulation is opposed; DCA concurs (opportunity-cost
objection only). Surfaced read-only through the coach.
"""
from types import SimpleNamespace as NS

from research.skeptic import dissent, audit_board_dissent


def _p(**kw):
    d = dict(symbol="X", action="dca", regime="RECOVERY", sharia_status="compliant",
             edge_allowed=False, hit_rate=0.0, sample_size=0, confidence=0.3)
    d.update(kw)
    return NS(**d)


def test_buy_is_never_a_clean_concur():
    d = dissent(_p(action="buy", edge_allowed=True, hit_rate=0.65, sample_size=80))
    assert d["stance"] in ("caution", "oppose")
    assert d["key_risks"] and d["invalidation_events"]


def test_thin_sample_buy_is_opposed():
    d = dissent(_p(action="buy", edge_allowed=True, hit_rate=0.65, sample_size=5))
    assert d["stance"] == "oppose"
    assert any("thin evidence" in r for r in d["key_risks"])


def test_buy_into_risk_off_is_opposed():
    d = dissent(_p(action="buy", edge_allowed=True, hit_rate=0.65, sample_size=80, regime="RECESSION_RISK"))
    assert d["stance"] == "oppose"


def test_dca_concurs_with_an_opportunity_cost_objection():
    d = dissent(_p(action="dca"))
    assert d["stance"] == "concur"
    assert any("opportunity cost" in r for r in d["key_risks"])


def test_noncompliant_accumulation_is_opposed():
    d = dissent(_p(action="dca", sharia_status="frozen"))
    assert d["stance"] == "oppose"
    assert any("Sharia-clear" in r for r in d["key_risks"])


def test_avoid_concurs_no_dissent():
    assert dissent(_p(action="avoid", sharia_status="frozen"))["stance"] == "concur"


def test_audit_orders_opposition_first():
    board = [_p(symbol="GOOD", action="dca"),
             _p(symbol="THIN", action="buy", edge_allowed=True, sample_size=5)]
    rows = audit_board_dissent(board)
    assert rows[0]["symbol"] == "THIN" and rows[0]["stance"] == "oppose"


def test_coach_surfaces_dissent(dbs):
    from sharia.whitelist import add_instrument
    from loop.opportunity_board import build_board
    from founder_tools.coach import coach
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    build_board(dbs, symbols=["SPUS"],
                edge_fn=lambda d, s: NS(trade_allowed=False, hit_rate=0.0, sample_size=0, reason="no edge"),
                persist=True)
    one = coach(dbs, "risks SPUS")
    assert "SKEPTIC on SPUS" in one and ("CONCUR" in one or "CAUTION" in one or "OPPOSE" in one)
    assert "structured dissent" in coach(dbs, "skeptic")

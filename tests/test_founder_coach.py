"""
camel-coach (Workstream C) — read-only Q&A over the governed state: routes intents, declines advice.
"""
import json
from types import SimpleNamespace as NS

from db.sqlite import connection
from founder_tools.coach import coach


def test_coach_status_has_gate_and_footer(dbs):
    out = coach(dbs, "status")
    assert "Live-money gate" in out
    assert "not financial or Sharia advice" in out          # the read-only footer is always present


def test_coach_declines_to_advise(dbs):
    out = coach(dbs, "should I buy SPUS right now?")
    assert "won't give a buy/sell recommendation" in out     # reports, never advises


def test_coach_board_and_why(dbs):
    from sharia.whitelist import add_instrument
    from loop.opportunity_board import build_board
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    build_board(dbs, symbols=["SPUS"],
                edge_fn=lambda d, s: NS(trade_allowed=True, hit_rate=0.65, sample_size=80,
                                        reason="edge confirmed"),
                persist=True)
    assert "SPUS" in coach(dbs, "show me the board")
    why = coach(dbs, "why SPUS")
    assert "SPUS" in why and "Reason chain" in why


def test_coach_regime(dbs):
    with connection(dbs.macro) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS regime_history ("
                     " id INTEGER PRIMARY KEY AUTOINCREMENT, classified_at TEXT, regime TEXT,"
                     " confidence REAL, signals TEXT, features TEXT)")
        conn.execute("INSERT INTO regime_history (classified_at, regime, confidence, signals, features) "
                     "VALUES (?,?,?,?,?)",
                     ("2026-06-11T00:00:00+00:00", "RECOVERY", 0.4, json.dumps(["benign"]), "{}"))
    assert "RECOVERY" in coach(dbs, "what's the regime?")


def test_coach_help_fallback(dbs):
    assert "Ask me about" in coach(dbs, "tell me a joke")

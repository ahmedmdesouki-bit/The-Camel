"""
S17.6 — the Opportunity Board: ranked, reasoned, governed proposals ("where to put the money").

The Edge verdict is injected so the assembly is deterministic. Covers: ranking (buy > dca > avoid),
Sharia-#1 hard wall (a 'proven edge' on a non-compliant name is still `avoid`), no-edge→DCA honesty,
full reason chains, that building the board moves NO money, board supersession, and risk-off tilt.
"""
from db.sqlite import connection
from sharia.whitelist import add_instrument
from loop.opportunity_board import build_board, current_board


class _Rep:
    def __init__(self, allowed, hit=0.6, n=60, reason="ok"):
        self.trade_allowed, self.hit_rate, self.sample_size, self.reason = allowed, hit, n, reason


def _edge(verdicts):
    """edge_fn stub: {symbol: (allowed, hit, n, reason)}; unknown symbols → no edge / no data."""
    def fn(_dbs, sym):
        v = verdicts.get(sym)
        return _Rep(*v) if v else _Rep(False, 0.0, 0, "no data")
    return fn


def _compliant(dbs, *syms):
    for s in syms:
        add_instrument(dbs.sharia, s, "etf", approved_by="founder", scan_id="t")


def test_board_ranks_buy_over_dca_over_avoid(dbs):
    _compliant(dbs, "SPUS", "HLAL")
    add_instrument(dbs.sharia, "HACK", "etf", approved_by="founder", scan_id="t",
                   sharia_status="non_compliant")
    edge = _edge({"SPUS": (True, 0.65, 80, "edge confirmed")})     # SPUS edge; HLAL none; HACK n/a
    board = build_board(dbs, symbols=["SPUS", "HLAL", "HACK"], edge_fn=edge)
    actions = {p.symbol: p.action for p in board}
    assert actions == {"SPUS": "buy", "HLAL": "dca", "HACK": "avoid"}
    assert board[0].symbol == "SPUS" and board[-1].symbol == "HACK"   # buy first, avoid last


def test_sharia_is_a_hard_wall_even_against_a_proven_edge(dbs):
    """Priority #1: a non-compliant name with a 'CONFIRMED' edge is still `avoid`, never `buy`."""
    add_instrument(dbs.sharia, "HACK", "etf", approved_by="founder", scan_id="t",
                   sharia_status="non_compliant")
    p = build_board(dbs, symbols=["HACK"], edge_fn=_edge({"HACK": (True, 0.95, 200, "huge edge")}))[0]
    assert p.action == "avoid" and p.score == 0.0


def test_no_edge_compliant_name_is_dca_not_failure(dbs):
    _compliant(dbs, "SPUS")
    p = build_board(dbs, symbols=["SPUS"], edge_fn=_edge({}))[0]
    assert p.action == "dca" and "DCA" in p.recommended_action and "success state" in p.recommended_action


def test_each_proposal_carries_a_full_reason_chain(dbs):
    _compliant(dbs, "SPUS")
    rc = build_board(dbs, symbols=["SPUS"], edge_fn=_edge({"SPUS": (True, 0.6, 80, "edge")}))[0].reason_chain
    assert any(r.startswith("Sharia:") for r in rc)
    assert any(r.startswith("Regime:") for r in rc)
    assert any(r.startswith("Edge:") for r in rc)


def test_building_the_board_moves_no_money(dbs):
    _compliant(dbs, "SPUS")
    build_board(dbs, symbols=["SPUS"], edge_fn=_edge({"SPUS": (True, 0.7, 80, "edge")}))
    with connection(dbs.portfolio) as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM positions").fetchone()[0] == 0
    assert all(r["status"] == "proposed" for r in current_board(dbs))      # proposals only


def test_rebuild_supersedes_the_prior_board(dbs):
    _compliant(dbs, "SPUS")
    build_board(dbs, symbols=["SPUS"], edge_fn=_edge({}))
    build_board(dbs, symbols=["SPUS"], edge_fn=_edge({}))
    with connection(dbs.learning) as conn:
        proposed = conn.execute(
            "SELECT COUNT(*) FROM opportunity_proposals WHERE status='proposed'").fetchone()[0]
        expired = conn.execute(
            "SELECT COUNT(*) FROM opportunity_proposals WHERE status='expired'").fetchone()[0]
    assert proposed == 1 and expired == 1
    assert len(current_board(dbs)) == 1


def test_risk_off_regime_lowers_the_score(dbs):
    _compliant(dbs, "SPUS")
    edge = _edge({"SPUS": (True, 0.6, 80, "edge")})
    calm = build_board(dbs, symbols=["SPUS"], edge_fn=edge, persist=False)[0].score
    with connection(dbs.macro) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS regime_history (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     " regime TEXT, confidence REAL, classified_at TEXT)")
        conn.execute("INSERT INTO regime_history (regime, confidence) VALUES ('RECESSION_RISK', 0.7)")
    risky = build_board(dbs, symbols=["SPUS"], edge_fn=edge, persist=False)[0].score
    assert risky < calm and risky > 0          # still a positive (proven) edge, just tilted defensive


def test_live_freeze_overrides_a_stale_pass_screen(dbs):
    """Review LOW: a frozen name with an OLD 'pass' screen row must still be `avoid` on the board — a live
    freeze wins over a stale screen (the Constitution blocks the buy anyway, but the board must be honest)."""
    from sharia.whitelist import freeze_instrument
    add_instrument(dbs.sharia, "DRIFT", "etf", approved_by="founder", scan_id="t")
    with connection(dbs.sharia) as conn:                      # a stale 'pass' screen on record
        conn.execute("CREATE TABLE IF NOT EXISTS sharia_status (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     " symbol TEXT, final_status TEXT)")
        conn.execute("INSERT INTO sharia_status (symbol, final_status) VALUES ('DRIFT','pass')")
    freeze_instrument(dbs.sharia, "DRIFT", "compliance drift")
    p = build_board(dbs, symbols=["DRIFT"], edge_fn=_edge({"DRIFT": (True, 0.9, 100, "edge")}))[0]
    assert p.sharia_status == "frozen" and p.action == "avoid"


def test_current_board_is_score_ordered(dbs):
    _compliant(dbs, "AAA", "BBB", "CCC")
    edge = _edge({"AAA": (True, 0.8, 90, "strong"), "BBB": (True, 0.55, 70, "ok")})  # CCC none → dca
    build_board(dbs, symbols=["AAA", "BBB", "CCC"], edge_fn=edge)
    board = current_board(dbs)
    scores = [r["score"] for r in board]
    assert scores == sorted(scores, reverse=True) and board[0]["symbol"] == "AAA"

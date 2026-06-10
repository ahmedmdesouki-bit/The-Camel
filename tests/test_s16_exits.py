"""
S16-A7 — governed exits: the generator of closes.

Pure rule evaluation (profit-take / stop-loss / time-stop / sharia_exit, stale-data skip), the governed
execution path (Constitution close-only + phantom/oversell guards + kill switch), and THE S16 Gate test:
one production `run_trading_tick` that exits a held position via the real PaperBroker, grades the run
'complete', resolves the round-trip, and moves a strategy base-rate — the loop closing end-to-end.
"""
from datetime import datetime, timedelta, timezone

import pytest

from db.sqlite import connection
from ledger.writer import append_entry
from broker.paper import PaperBroker
from broker.positions import held_qty, get_position
from guardrail.constitution import Action, ActionType, PortfolioState, Instrument, Thesis, Decision
from sharia.whitelist import add_instrument, freeze_instrument
from data.store import store_price
from loop.assembled import AssembledLoop
from loop.jobs import run_trading_tick
from learning.measure import record_trade_decision
from trader.execution.exits import (
    ExitProposal, evaluate_exits, build_exit_proposals, DEFAULT_EXIT_RULES,
)


def _wl(status="compliant", frozen=False):
    return {"AAPL": Instrument(symbol="AAPL", sector="tech", sharia_status=status,
                               frozen=frozen, on_whitelist=True)}


def _pos(sym="AAPL", qty=10.0, avg=100.0, opened_days_ago=1):
    opened = (datetime.now(timezone.utc) - timedelta(days=opened_days_ago)).isoformat()
    return {"symbol": sym, "qty": qty, "avg_cost": avg, "opened_at": opened}


# ================= pure rules =================

def test_profit_take_triggers():
    props, skipped = evaluate_exits([_pos()], {"AAPL": 120.0}, _wl())   # +20% ≥ +15%
    assert skipped == [] and len(props) == 1
    p = props[0]
    assert p.rule == "profit_take" and p.qty == 10.0 and p.notional_usd == 1200.0


def test_stop_loss_triggers():
    props, _ = evaluate_exits([_pos()], {"AAPL": 90.0}, _wl())          # −10% ≤ −8%
    assert props and props[0].rule == "stop_loss"


def test_time_stop_triggers():
    props, _ = evaluate_exits([_pos(opened_days_ago=120)], {"AAPL": 101.0}, _wl())
    assert props and props[0].rule == "time_stop"


def test_sharia_exit_outranks_everything():
    props, _ = evaluate_exits([_pos()], {"AAPL": 120.0}, _wl(frozen=True))
    assert props and props[0].rule == "sharia_exit"


def test_quiet_position_proposes_nothing():
    props, _ = evaluate_exits([_pos()], {"AAPL": 103.0}, _wl())         # +3%, young, compliant
    assert props == []


def test_no_price_skips_never_exits_blind():
    props, skipped = evaluate_exits([_pos()], {}, _wl(frozen=True))     # even a Sharia exit needs a price
    assert props == [] and skipped == ["AAPL"]


def test_founder_limits_override_defaults():
    limits = {"exit_profit_take_pct": 0.30}                             # founder loosened the take
    props, _ = evaluate_exits([_pos()], {"AAPL": 120.0}, _wl(), limits=limits)
    assert props == []                                                  # +20% < +30% → hold
    assert DEFAULT_EXIT_RULES["exit_profit_take_pct"] == 0.15           # defaults untouched


# ================= governed execution =================

def _seed_book(dbs, price=100.0, cash=1000.0, notional=500.0):
    """Whitelist AAPL, seed a price, deposit cash, and buy through the real broker."""
    add_instrument(dbs.sharia, "AAPL", "etf", approved_by="founder", scan_id="t-1")
    store_price(dbs.market, {"symbol": "AAPL", "date": "2026-01-02", "open": price, "high": price,
                             "low": price, "close": price, "volume": 1000, "adj_close": price})
    append_entry(dbs.portfolio, "DEPOSIT", "", cash)
    broker = PaperBroker(dbs.portfolio, dbs.market)
    broker.submit(Action(ActionType.TRADE, symbol="AAPL", side="buy", notional_usd=notional,
                         thesis=Thesis("inv", "+15%", "90d"), mode="paper"),
                  Decision(allow=True, reason="test"))
    return broker


def test_run_exits_closes_through_real_broker(dbs):
    broker = _seed_book(dbs)
    store_price(dbs.market, {"symbol": "AAPL", "date": "2026-01-03", "open": 120, "high": 120,
                             "low": 120, "close": 120.0, "volume": 1000, "adj_close": 120.0})
    from sharia.whitelist import load_whitelist
    wl = load_whitelist(dbs.sharia)
    proposals, mtm, _ = build_exit_proposals(dbs, wl)
    assert proposals and proposals[0].rule == "profit_take"

    state = PortfolioState(fund_usd=1100, cash_usd=500, positions=dict(mtm), whitelist=wl)
    loop = AssembledLoop(dbs, broker_execute=lambda a: broker.submit(a, Decision(True, "ok")))
    outcomes = loop.run_exits(proposals, state)

    assert outcomes and outcomes[0].stage == "executed"
    assert held_qty(dbs.portfolio, "AAPL") == 0                          # closed for real
    assert get_position(dbs.portfolio, "AAPL").realized_pnl > 0         # +20% round-trip banked
    with connection(dbs.portfolio) as conn:
        assert conn.execute("SELECT COUNT(*) FROM ledger WHERE type='SELL'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM op_log WHERE event_type='EXIT'").fetchone()[0] >= 1


def test_mark_to_market_prevents_false_oversell(dbs):
    """Bought at 100, price now 120: the sell notional (qty×120) exceeds the stale fill-price value —
    without the mtm refresh the Constitution's oversell guard would block an honest full close."""
    broker = _seed_book(dbs)
    store_price(dbs.market, {"symbol": "AAPL", "date": "2026-01-03", "open": 120, "high": 120,
                             "low": 120, "close": 120.0, "volume": 1000, "adj_close": 120.0})
    from sharia.whitelist import load_whitelist
    wl = load_whitelist(dbs.sharia)
    proposals, mtm, _ = build_exit_proposals(dbs, wl)
    # WITHOUT refresh: stale value (5 shares × $100 fill = $500) vs notional $600 → blocked
    stale = PortfolioState(fund_usd=1100, cash_usd=500,
                           positions={"AAPL": 500.0}, whitelist=wl)
    loop = AssembledLoop(dbs, broker_execute=lambda a: broker.submit(a, Decision(True, "ok")))
    blocked = loop.run_exits(proposals, stale)
    assert blocked[0].stage == "edge_or_constitution" and "exceeds held" in blocked[0].reason.lower()
    # WITH refresh (what run_trading_tick does): allowed and filled
    fresh = PortfolioState(fund_usd=1100, cash_usd=500, positions=dict(mtm), whitelist=wl)
    ok = loop.run_exits(proposals, fresh)
    assert ok[0].stage == "executed"


def test_frozen_name_exit_is_allowed_close_only(dbs):
    """The Constitution blocks BUYING a frozen name but allows the de-risking SELL — proven through
    the real gate."""
    broker = _seed_book(dbs)
    freeze_instrument(dbs.sharia, "AAPL", "compliance drift (test)")
    from sharia.whitelist import load_whitelist
    wl = load_whitelist(dbs.sharia)
    proposals, mtm, _ = build_exit_proposals(dbs, wl)
    assert proposals[0].rule == "sharia_exit"
    state = PortfolioState(fund_usd=1100, cash_usd=500, positions=dict(mtm), whitelist=wl)
    loop = AssembledLoop(dbs, broker_execute=lambda a: broker.submit(a, Decision(True, "ok")))
    outcomes = loop.run_exits(proposals, state)
    assert outcomes[0].stage == "executed" and held_qty(dbs.portfolio, "AAPL") == 0


def test_kill_switch_halts_exits(dbs):
    from ops.kill_switch import halt
    broker = _seed_book(dbs)
    halt()
    loop = AssembledLoop(dbs, broker_execute=lambda a: broker.submit(a, Decision(True, "ok")))
    out = loop.run_exits([ExitProposal("AAPL", 5.0, 600.0, "profit_take", "t")],
                         PortfolioState(fund_usd=1100, cash_usd=500))
    assert out == [] and held_qty(dbs.portfolio, "AAPL") > 0            # nothing moved


# ================= THE S16 Gate, end-to-end through the production entrypoint =================

def _write_yaml(tmp_path, phase=0):
    p = tmp_path / "limits.yaml"
    p.write_text(f"phase: {phase}\nmax_position_pct: 0.20\nper_order_envelope_usd: 50\n", encoding="utf-8")
    return str(p)


def test_production_tick_exits_resolves_and_learns_end_to_end(dbs, tmp_path):
    """ONE scheduled `run_trading_tick`: a held position hits its profit-take → the governed exit fills
    via the real PaperBroker → the run grades 'complete' (real Act work) → Measure resolves the closed
    round-trip → the strategy base-rate MOVES. The loop, closed, in production."""
    _seed_book(dbs)                                                     # buy 5 sh AAPL @ 100
    record_trade_decision(dbs, "AAPL", ["e2e_exit"])                    # what the buy tick's Measure does
    store_price(dbs.market, {"symbol": "AAPL", "date": "2026-01-03", "open": 120, "high": 120,
                             "low": 120, "close": 120.0, "volume": 1000, "adj_close": 120.0})

    out = run_trading_tick(dbs, symbols=[], config_path=_write_yaml(tmp_path))

    assert out["exits"] == ["AAPL"]                                     # the exit fired in production
    assert out["outcome"] == "complete"                                 # exits count as real Act work
    assert held_qty(dbs.portfolio, "AAPL") == 0                         # round-trip done
    assert out["learning"]["round_trips"] == 1                          # Measure resolved it
    upd = {s["strategy_id"]: s for s in out["learning"]["strategies_updated"]}
    assert upd["e2e_exit"]["n"] == 1 and upd["e2e_exit"]["base_rate"] > 0.5   # a WIN moved the rate
    with connection(dbs.portfolio) as conn:
        row = conn.execute("SELECT outcome FROM runs WHERE id=?", (out["run_id"],)).fetchone()
    assert row["outcome"] == "complete"                                 # the readiness clock advanced


def test_quiet_book_still_grades_no_action(dbs, tmp_path):
    """A funded book whose position triggers NO exit rule and whose router waits stays 'no_action' —
    exits don't accidentally inflate the readiness clock."""
    _seed_book(dbs)
    store_price(dbs.market, {"symbol": "AAPL", "date": "2026-01-03", "open": 103, "high": 103,
                             "low": 103, "close": 103.0, "volume": 1000, "adj_close": 103.0})
    out = run_trading_tick(dbs, symbols=[], config_path=_write_yaml(tmp_path))
    assert out["exits"] == [] and out["outcome"] == "no_action"


# ================= QA-FAIL regressions (the offense-sprint review) =================

def test_fractional_position_full_close_blocker(dbs, tmp_path):
    """THE BLOCKER: ugly floats. A $50 buy at $30.4398 yields a fractional qty whose notional
    round-trip (qty×close → notional/close) lands above the broker's absolute 1e-9 guard ~36% of the
    time when rounded. The exact-notional sizing + the broker's full-close clamp must close it
    completely — no refusal, no dust, status='closed' — through the PRODUCTION tick."""
    add_instrument(dbs.sharia, "AAPL", "etf", approved_by="founder", scan_id="t-1")
    store_price(dbs.market, {"symbol": "AAPL", "date": "2026-01-02", "open": 30.4398, "high": 30.4398,
                             "low": 30.4398, "close": 30.4398, "volume": 1000, "adj_close": 30.4398})
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)
    PaperBroker(dbs.portfolio, dbs.market).submit(
        Action(ActionType.TRADE, symbol="AAPL", side="buy", notional_usd=50.0,
               thesis=Thesis("inv", "+15%", "90d"), mode="paper"),
        Decision(allow=True, reason="test"))
    record_trade_decision(dbs, "AAPL", ["frac"])             # what the buy tick's Measure step does
    store_price(dbs.market, {"symbol": "AAPL", "date": "2026-01-03", "open": 39.0173, "high": 39.0173,
                             "low": 39.0173, "close": 39.0173, "volume": 1000, "adj_close": 39.0173})

    out = run_trading_tick(dbs, symbols=[], config_path=_write_yaml(tmp_path))

    assert out["exits"] == ["AAPL"] and out["outcome"] == "complete"
    pos = get_position(dbs.portfolio, "AAPL")
    assert pos.qty == 0 and pos.status == "closed"           # fully closed — no dust, no refusal
    assert out["learning"]["round_trips"] == 1               # and the round-trip RESOLVED


def test_exit_fill_refusal_grades_run_error_loudly(dbs, tmp_path):
    """QA: a broker-refused de-risking order must grade the run 'error' (non-counting) — never an
    invisible op_log row while the run reads 'complete'/'no_action'."""
    _seed_book(dbs)
    store_price(dbs.market, {"symbol": "AAPL", "date": "2026-01-03", "open": 120, "high": 120,
                             "low": 120, "close": 120.0, "volume": 1000, "adj_close": 120.0})

    class _RefusingBroker:
        def submit(self, action, decision, **kw):
            raise RuntimeError("broker connection lost")
    out = run_trading_tick(dbs, symbols=[], config_path=_write_yaml(tmp_path),
                           broker=_RefusingBroker())
    assert out["outcome"] == "error" and out["exit_errors"]
    with connection(dbs.portfolio) as conn:
        row = conn.execute("SELECT outcome, ended_at FROM runs ORDER BY id DESC LIMIT 1").fetchone()
    assert row["outcome"] == "error" and row["ended_at"] is not None
    from ops.live_readiness import _paper_runs
    assert _paper_runs(dbs) == 0                             # a failed de-risk never advances the clock


def test_blocked_buy_leg_does_not_grade_complete(dbs, tmp_path, monkeypatch):
    """QA: router=='trader' alone must not count as Act — if every candidate is blocked/withheld
    (zero fills, zero exits) the run is 'no_action', not 'complete'."""
    import loop.driver as driver_mod
    from loop.assembled import TickResult, ActionOutcome
    append_entry(dbs.portfolio, "DEPOSIT", "", 1000.0)

    def _routed_but_all_blocked(*a, **k):
        return TickResult(router_path="trader", router_reason="edge proven",
                          outcomes=[ActionOutcome("AAPL", "approval", False, "awaiting human approval")])
    monkeypatch.setattr(driver_mod, "run_strategy_tick", _routed_but_all_blocked)
    out = run_trading_tick(dbs, symbols=["AAPL"], config_path=_write_yaml(tmp_path, phase=1))
    assert out["executed"] == [] and out["outcome"] == "no_action"


def test_phase1_exit_is_withheld_until_human_approves(dbs):
    """QA: the live-phase approval rail on EXITS was untested. Default withholds (held qty unchanged,
    stage 'approval'); an explicit approval executes."""
    broker = _seed_book(dbs)
    store_price(dbs.market, {"symbol": "AAPL", "date": "2026-01-03", "open": 120, "high": 120,
                             "low": 120, "close": 120.0, "volume": 1000, "adj_close": 120.0})
    from sharia.whitelist import load_whitelist
    wl = load_whitelist(dbs.sharia)
    proposals, mtm, _ = build_exit_proposals(dbs, wl)
    state = PortfolioState(fund_usd=1100, cash_usd=500, positions=dict(mtm), whitelist=wl)
    exe = lambda a: broker.submit(a, Decision(True, "ok"))

    held_before = held_qty(dbs.portfolio, "AAPL")
    withheld = AssembledLoop(dbs, phase=1, broker_execute=exe).run_exits(proposals, state)
    assert withheld[0].stage == "approval" and not withheld[0].approved
    assert held_qty(dbs.portfolio, "AAPL") == held_before    # nothing moved without a human

    approved = AssembledLoop(dbs, phase=1, broker_execute=exe,
                             approval_fn=lambda a: True).run_exits(proposals, state)
    assert approved[0].stage == "executed" and held_qty(dbs.portfolio, "AAPL") == 0


def test_reopened_position_age_clock_restarts(dbs):
    """QA churn-loop regression: buy → close → re-buy must restart opened_at; otherwise every
    re-bought name is instantly time-stopped off the FIRST-ever open date."""
    from broker.positions import apply_fill
    from trader.execution.exits import open_positions
    apply_fill(dbs.portfolio, "AAPL", "buy", 10, 100.0)
    with connection(dbs.portfolio) as conn:                  # age the original open by 120 days
        conn.execute("UPDATE positions SET opened_at=? WHERE symbol='AAPL'",
                     ((datetime.now(timezone.utc) - timedelta(days=120)).isoformat(),))
    apply_fill(dbs.portfolio, "AAPL", "sell", 10, 110.0)     # close
    apply_fill(dbs.portfolio, "AAPL", "buy", 10, 100.0)      # re-open → NEW round-trip, fresh clock
    rows = open_positions(dbs.portfolio)                     # the REAL positions-table lifecycle
    props, _ = evaluate_exits(rows, {"AAPL": 101.0}, _wl())
    assert props == []                                       # young re-entry → no time_stop


def test_unlisted_holding_is_proposed_and_visibly_blocked(dbs):
    """QA dead-end regression: a held name with NO whitelist row is proposed ('unlisted_holding') so
    the Constitution's refusal is VISIBLE every tick instead of an invisible trap."""
    props, _ = evaluate_exits([_pos()], {"AAPL": 100.0}, {})  # empty whitelist
    assert props and props[0].rule == "unlisted_holding"
    loop = AssembledLoop(dbs, broker_execute=lambda a: "never reached")
    out = loop.run_exits(props, PortfolioState(fund_usd=1000, cash_usd=0,
                                               positions={"AAPL": 1000.0}))
    assert out[0].stage == "edge_or_constitution" and "whitelist" in out[0].reason.lower()


def test_exit_limits_sanity_check_refuses_sign_typos():
    """QA: a one-character sign typo must fail LOUDLY, not liquidate the book in one tick."""
    with pytest.raises(ValueError):
        evaluate_exits([_pos()], {"AAPL": 100.0}, _wl(), limits={"exit_stop_loss_pct": 0.08})
    with pytest.raises(ValueError):
        evaluate_exits([_pos()], {"AAPL": 100.0}, _wl(), limits={"exit_profit_take_pct": -0.15})
    with pytest.raises(ValueError):
        evaluate_exits([_pos()], {"AAPL": 100.0}, _wl(), limits={"exit_time_stop_days": 0})


def test_mtm_resyncs_fund_total(dbs):
    """QA rail regression: marking positions without recomputing fund_usd skews the concentration and
    cash-buffer rails. _apply_mtm must keep cash + Σ positions == fund."""
    from loop.jobs import _apply_mtm
    state = PortfolioState(fund_usd=1000.0, cash_usd=500.0, positions={"AAPL": 500.0})
    _apply_mtm(state, {"AAPL": 350.0})                       # the book depreciated since the fill
    assert state.positions["AAPL"] == 350.0
    assert state.fund_usd == 850.0                           # 500 cash + 350 marked — never stale 1000

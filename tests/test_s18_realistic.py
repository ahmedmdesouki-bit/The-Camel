"""
S18 — Production-Paper Integrity: the realistic broker (spread/fees/whole-share, honest non-fill) and the
investment-valid vs operational run distinction (only realistic runs advance the >=28-run readiness clock).
"""
import pytest

from db.sqlite import connection
from ledger.writer import append_entry
from data.store import store_price
from sharia.whitelist import add_instrument
from broker.positions import held_qty
from broker.paper import NoMarketPriceError
from broker.realistic import RealisticPaperBroker, NoFillError
from guardrail.constitution import Action, ActionType, Thesis, Decision
from loop.jobs import run_trading_tick
from ops.live_readiness import _paper_runs
from trader.strategies.registry import StrategyRegistry
from trader.strategies.core_dca import CoreDCA


def _bar(dbs, symbol="SPUS", close=50.0, volume=1_000_000):
    store_price(dbs.market, {"symbol": symbol, "date": "2026-06-11", "open": close, "high": close,
                             "low": close, "close": close, "volume": volume, "adj_close": close})


def _buy(symbol="SPUS", notional=500.0):
    return Action(ActionType.TRADE, symbol=symbol, side="buy", notional_usd=notional,
                  thesis=Thesis("inv", "+15%", "90d"), mode="paper")


def _yaml(tmp_path, phase=0):
    p = tmp_path / "limits.yaml"
    p.write_text(f"phase: {phase}\nmax_position_pct: 0.50\nper_order_envelope_usd: 1000\n", encoding="utf-8")
    return str(p)


# ---------------- the realistic broker (buys) ----------------

def test_realistic_buy_crosses_spread_and_charges_fees(dbs):
    _bar(dbs, "SPUS", close=50.0)
    b = RealisticPaperBroker(dbs.portfolio, dbs.market, spread_bps=10.0, fee_bps=2.0)
    fill = b.submit(_buy("SPUS", 500.0), Decision(True, "ok"))
    assert fill.filled_qty == 9                         # floor(500 / 50.025) — whole shares
    assert fill.fill_price > 50.0                       # paid the ask (crossed the spread), not the close
    assert fill.fees > 0
    assert held_qty(dbs.portfolio, "SPUS") == 9
    with connection(dbs.portfolio) as conn:
        amt = conn.execute("SELECT amount FROM ledger WHERE type='BUY' ORDER BY id DESC LIMIT 1").fetchone()[0]
    assert amt < -(9 * 50.0)                            # cash out exceeds mid*qty (spread + fees)


def test_realistic_below_one_share_is_an_honest_nonfill(dbs):
    _bar(dbs, "SPUS", close=55.0)
    b = RealisticPaperBroker(dbs.portfolio, dbs.market)
    with pytest.raises(NoFillError):                    # $50 < one whole share at $55 — refused, not fabricated
        b.submit(_buy("SPUS", 50.0), Decision(True, "ok"))
    assert held_qty(dbs.portfolio, "SPUS") == 0


def test_realistic_no_bar_refuses(dbs):
    b = RealisticPaperBroker(dbs.portfolio, dbs.market)
    with pytest.raises(NoMarketPriceError):
        b.submit(_buy("NOPE", 500.0), Decision(True, "ok"))


def test_realistic_sell_delegates_to_last_close(dbs):
    _bar(dbs, "SPUS", close=50.0)
    b = RealisticPaperBroker(dbs.portfolio, dbs.market)
    b.submit(_buy("SPUS", 500.0), Decision(True, "ok"))     # establish 9 shares
    held = held_qty(dbs.portfolio, "SPUS")
    assert held == 9
    sell = Action(ActionType.TRADE, symbol="SPUS", side="sell", notional_usd=held * 50.0,
                  thesis=Thesis("inv", "+15%", "90d"), mode="paper")
    fill = b.submit(sell, Decision(True, "ok"))             # de-risk at last close (no spread)
    assert fill.fill_price == 50.0                          # PaperBroker last-close fill, not the realistic touch
    assert held_qty(dbs.portfolio, "SPUS") == 0


# ---------------- the readiness-clock distinction ----------------

def test_realistic_production_tick_counts_toward_clock(dbs, tmp_path):
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    _bar(dbs, "SPUS", close=50.0)
    append_entry(dbs.portfolio, "DEPOSIT", "", 10000.0)
    reg = StrategyRegistry()
    reg.register(CoreDCA())
    out = run_trading_tick(dbs, symbols=["SPUS"], config_path=_yaml(tmp_path), registry=reg,
                           realistic=True, notional_per_trade=500.0)
    assert out["paper_mode"] == "investment_valid"
    assert out["executed"] == ["SPUS"] and out["outcome"] == "complete"
    assert _paper_runs(dbs) == 1                            # realistic run DOES advance the clock


def test_realistic_tick_below_one_share_no_action(dbs, tmp_path):
    add_instrument(dbs.sharia, "SPUS", "etf", approved_by="founder", scan_id="t")
    _bar(dbs, "SPUS", close=55.0)
    append_entry(dbs.portfolio, "DEPOSIT", "", 10000.0)
    reg = StrategyRegistry()
    reg.register(CoreDCA())
    out = run_trading_tick(dbs, symbols=["SPUS"], config_path=_yaml(tmp_path), registry=reg,
                           realistic=True, notional_per_trade=50.0)   # $50 < one share @ $55
    assert out["executed"] == [] and out["outcome"] == "no_action"
    assert _paper_runs(dbs) == 0

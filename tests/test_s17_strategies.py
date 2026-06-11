"""
S17 — the missing backlog strategies, built: ts_momentum, mean_reversion, dca_ladder.

Pure signal logic (no I/O), so they are deterministic and unit-tested directly. Each is a PROPOSER only;
the full Edge Proof + Constitution still gate every signal downstream, and none is auto-added to the live
production roster — a new strategy EARNS its place via the Edge Lab (the promotion philosophy), so these
ship available-in-the-registry but un-promoted.
"""
from trader.strategies.base import StrategyContext
from trader.strategies.momentum import TimeSeriesMomentum, trailing_return, above_trend
from trader.strategies.mean_reversion import MeanReversion, pct_below_ma
from trader.strategies.dca_ladder import DCALadder, drawdown_from_high, ladder_rungs


def _rising(n=260, start=100.0, step=0.5):
    return [start + i * step for i in range(n)]


def _falling(n=261, start=300.0, step=0.5):
    return [start - i * step for i in range(n)]


def _ctx(closes_by_sym, regime="RECOVERY"):
    return StrategyContext(regime=regime, closes=closes_by_sym,
                           whitelist={s: "compliant" for s in closes_by_sym})


# ---------------- ts_momentum (absolute / time-series) ----------------

def test_ts_momentum_buys_positive_own_trend():
    sigs = TimeSeriesMomentum().generate_signals(_ctx({"SPUS": _rising()}))
    assert sigs and sigs[0].action == "buy" and sigs[0].symbol == "SPUS"


def test_ts_momentum_silent_in_downtrend():
    assert TimeSeriesMomentum().generate_signals(_ctx({"SPUS": _falling()})) == []


def test_trailing_return_and_trend_need_history():
    assert trailing_return([100, 101, 102]) == 0.0
    assert above_trend([100, 101, 102]) is False


# ---------------- mean_reversion (dip-buy with falling-knife guard) ----------------

def _uptrend_with_dip():
    s = [100 + i * 0.5 for i in range(219)]      # long uptrend -> well above the 200d MA
    s.append(s[-1] * 0.93)                        # a sharp recent dip below the short MA
    return s


def test_mean_reversion_buys_dip_inside_uptrend():
    closes = _uptrend_with_dip()
    assert pct_below_ma(closes) >= 0.03
    sigs = MeanReversion().generate_signals(_ctx({"SPUS": closes}))
    assert sigs and sigs[0].action == "buy"


def test_mean_reversion_refuses_falling_knife():
    s = _falling()
    s.append(s[-1] * 0.93)                         # a dip, but the long trend is broken (below 200d MA)
    assert MeanReversion().generate_signals(_ctx({"SPUS": s})) == []


# ---------------- dca_ladder (ETF-only tranche DCA + deterioration guard) ----------------

def _peak_then_pullback():
    s = [100 + i * 0.5 for i in range(250)]       # rise to ~224
    s += [s[-1] * (1 - 0.015 * k) for k in range(1, 8)]   # ~10% pullback over 7 bars
    return s


def test_dca_ladder_buys_etf_dip_above_trend():
    closes = _peak_then_pullback()
    assert drawdown_from_high(closes) >= 0.05 and ladder_rungs(closes) >= 1
    sigs = DCALadder().generate_signals(_ctx({"SPUS": closes}))
    assert sigs and sigs[0].action == "buy" and sigs[0].symbol == "SPUS"


def test_dca_ladder_never_ladders_a_single_stock():
    """RULE 1 (the DO-NOT rail): the SAME dip on a NON-ETF name is refused — never average down a stock."""
    closes = _peak_then_pullback()
    assert DCALadder().generate_signals(_ctx({"AAPL": closes})) == []


def test_dca_ladder_stops_when_trend_breaks():
    """RULE 3 (deterioration guard): an ETF below its 200d trend is a falling knife — no tranche."""
    assert DCALadder().generate_signals(_ctx({"SPUS": _falling()})) == []

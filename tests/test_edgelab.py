"""
S12b — Edge Lab: the two-engine cross-check, cost-aware returns, beats-DCA, walk-forward honesty
guards, and the No-Edge protocol (no proven edge → systematic DCA, never idle on opportunity).
"""
from trader.edgelab.backtest import run_backtest, run_event_driven, run_vectorized
from trader.edgelab.honest import walk_forward_split, survives_out_of_sample, passes_crisis
from trader.edgelab.no_edge import resolve_no_edge, beats_dca, DCA_FALLBACK


# closes with a sharp dip a smart signal can sidestep
_CLOSES = [100.0, 110.0, 90.0, 120.0, 130.0]
_SMART = [1, 0, 1, 1, 1]      # flat through the 110→90 drop
_ALWAYS = [1, 1, 1, 1, 1]


# ---------------- two-engine cross-check ----------------

def test_engines_agree():
    r = run_backtest(_CLOSES, _SMART, cost_bps=20)
    assert r.engines_agree                                   # vectorized == event-driven
    assert abs(run_event_driven(_CLOSES, _SMART, 20) - run_vectorized(_CLOSES, _SMART, 20)) < 1e-9


def test_costs_reduce_return_and_trades_counted():
    r = run_backtest(_CLOSES, _SMART, cost_bps=20)
    assert r.net_return < r.gross_return                     # cost drag
    assert r.n_trades == 3                                    # entry, exit at bar1, re-entry at bar2


def test_smart_signal_beats_dca_through_the_dip():
    r = run_backtest(_CLOSES, _SMART, cost_bps=20)
    assert r.beats_dca and r.net_return > r.dca_return       # sidesteps the drawdown


def test_always_in_equals_dca_and_does_not_beat_it():
    r = run_backtest(_CLOSES, _ALWAYS, cost_bps=20)
    assert abs(r.net_return - r.dca_return) < 1e-9 and not r.beats_dca
    assert r.max_drawdown < 0                                 # always-in eats the dip


# ---------------- honesty guards ----------------

def test_walk_forward_split_is_out_of_sample():
    train, test = walk_forward_split(10, train_frac=0.7)
    assert train == list(range(7)) and test == [7, 8, 9] and not set(train) & set(test)


def test_overfit_guard():
    assert survives_out_of_sample(train_return=0.20, test_return=0.12) is True   # 60% survives
    assert survives_out_of_sample(train_return=0.20, test_return=0.04) is False  # collapsed → overfit
    assert survives_out_of_sample(train_return=0.20, test_return=-0.01) is False # negative OOS


def test_crisis_floor():
    assert passes_crisis({"gfc_2008": -0.20, "covid_2020": -0.30}, max_drawdown=-0.35) is True
    assert passes_crisis({"gfc_2008": -0.50}, max_drawdown=-0.35) is False


# ---------------- No-Edge protocol ----------------

def test_no_edge_falls_back_to_dca():
    assert resolve_no_edge(edge_allowed=False, has_capital=True).path == DCA_FALLBACK
    assert resolve_no_edge(edge_allowed=False, has_capital=False).path == "wait"


def test_active_strategy_needs_edge_and_to_beat_dca():
    assert resolve_no_edge(True, beats_dca=True).path == "active_strategy"
    assert resolve_no_edge(True, beats_dca=False).path == DCA_FALLBACK   # edge but loses to DCA → DCA
    assert beats_dca(0.12, 0.10) and not beats_dca(0.10, 0.10)

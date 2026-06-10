"""
S16-A5 (evidence-gated promotion: a rung is EARNED) + the Edge Lab run harness (the one-command
EDGE / NO_EDGE→DCA verdict on real stored history).
"""
import math

import pytest

from data.store import store_price
from learning.measure import strategy_evidence, record_trade_decision, resolve_and_learn
from broker.positions import apply_fill
from trader.strategies.registry import StrategyRegistry, PromotionEvidenceError
from trader.strategies.base import PromotionMode
from trader.strategies.quality_momentum import QualityMomentum
from trader.edgelab.run import (
    evaluate_symbol, sma_trend_signals, momentum_signals, MIN_BARS,
)


# ================= A5 — promotion is earned =================

def test_promote_without_evidence_is_refused():
    reg = StrategyRegistry(); reg.register(QualityMomentum())
    with pytest.raises(PromotionEvidenceError):
        reg.promote("quality_momentum")                      # the audit's "free state-setter" is closed
    assert reg.get("quality_momentum").meta.mode == PromotionMode.BACKTEST   # rung unchanged


def test_promote_with_thin_or_weak_evidence_is_refused():
    reg = StrategyRegistry(); reg.register(QualityMomentum())
    with pytest.raises(PromotionEvidenceError):
        reg.promote("quality_momentum", evidence={"base_rate": 0.9, "n": 5})    # too few round-trips
    with pytest.raises(PromotionEvidenceError):
        reg.promote("quality_momentum", evidence={"base_rate": 0.3, "n": 50})   # record refutes it


def test_promote_with_real_track_record_advances_one_rung():
    reg = StrategyRegistry(); reg.register(QualityMomentum())
    mode = reg.promote("quality_momentum", evidence={"base_rate": 0.62, "n": 30})
    assert mode == PromotionMode.REALISTIC_PAPER


def test_founder_override_is_explicit_and_named():
    reg = StrategyRegistry(); reg.register(QualityMomentum())
    assert reg.promote("quality_momentum", by_founder="Chiko") == PromotionMode.REALISTIC_PAPER
    with pytest.raises(PromotionEvidenceError):
        reg.promote("quality_momentum", by_founder="   ")    # a blank name is not an override


def test_strategy_evidence_reads_the_real_track_record(dbs):
    assert strategy_evidence(dbs, "alpha")["n"] == 0         # no record yet → ungrantable
    record_trade_decision(dbs, "AAPL", ["alpha"])
    apply_fill(dbs.portfolio, "AAPL", "buy", 10, 100.0)
    apply_fill(dbs.portfolio, "AAPL", "sell", 10, 120.0)
    resolve_and_learn(dbs)
    ev = strategy_evidence(dbs, "alpha")
    assert ev["n"] == 1 and ev["wins"] == 1 and ev["base_rate"] > 0.5


# ================= Edge Lab harness =================

def _seed_history(dbs, symbol, closes):
    # strictly chronological ISO dates — the loader ORDERs BY date, so a non-monotonic fixture would
    # permute the series and test a scrambled market (QA finding on the previous fixture)
    from datetime import date, timedelta
    base = date(2018, 1, 1)
    for i, c in enumerate(closes):
        store_price(dbs.market, {"symbol": symbol, "date": (base + timedelta(days=i)).isoformat(),
                                 "open": c, "high": c, "low": c, "close": c,
                                 "volume": 1000, "adj_close": c})


def test_signal_rules_use_only_past_data():
    closes = [100.0] * 10 + [200.0]                          # the jump is at the LAST bar
    sigs = sma_trend_signals(closes, n=5)
    assert sigs[:10] == [0] * 10                             # flat closes → never above the SMA before the jump
    assert sigs[10] == 1                                     # reacts AT the jump bar, not before
    m = momentum_signals(closes, lookback=5)
    assert all(s == 0 for s in m[:10]) and m[10] == 1


def test_insufficient_data_yields_no_verdict(dbs):
    _seed_history(dbs, "THIN", [100.0 + i for i in range(30)])
    out = evaluate_symbol(dbs.market, "THIN")
    assert out["verdict"] == "insufficient_data" and out["bars"] == 30 and out["needed"] == MIN_BARS


def test_trending_series_produces_a_structured_verdict(dbs):
    # a steady uptrend with mild noise — enough bars for an honest split
    closes = [100.0 * math.exp(0.001 * i) * (1 + 0.01 * ((-1) ** i)) for i in range(300)]
    _seed_history(dbs, "TREND", closes)
    out = evaluate_symbol(dbs.market, "TREND", rule="sma_trend")
    assert out["verdict"] in ("EDGE", "NO_EDGE_DCA")         # a verdict, honestly derived
    assert out["engines_agree"] is True                      # the two engines cross-check
    assert out["bars"] == 300 and isinstance(out["beats_dca"], bool)
    assert out["path"] in ("active_strategy", "core_dca")


def test_no_edge_resolves_to_dca_not_failure(dbs):
    # a mean-reverting square wave: trend-following SHOULD find no edge here → the humble DCA path
    closes = [100.0 + (5.0 if i % 2 else -5.0) for i in range(300)]
    _seed_history(dbs, "CHOP", closes)
    out = evaluate_symbol(dbs.market, "CHOP", rule="sma_trend")
    assert out["verdict"] == "NO_EDGE_DCA" and out["path"] == "core_dca"


def test_steady_true_edge_can_actually_pass_oos(dbs):
    """QA regression: with raw 70/30 segment totals a perfectly steady edge maxed out at a test/train
    ratio of ~0.43 < 0.5, so EDGE was mathematically unreachable. Per-bar normalization fixes it: a
    constant uptrend captured perfectly by the rule must survive out-of-sample."""
    import math as _m
    closes = [100.0 * _m.exp(0.002 * i) for i in range(400)]    # steady drift, zero noise
    _seed_history(dbs, "DRIFT", closes)
    out = evaluate_symbol(dbs.market, "DRIFT", rule="sma_trend")
    assert out["survives_out_of_sample"] is True                 # the bar is now passable
    # and the verdict is internally consistent with its inputs
    if out["verdict"] == "EDGE":
        assert out["survives_out_of_sample"] and out["engines_agree"] and out["beats_dca"]
    else:
        assert not (out["survives_out_of_sample"] and out["engines_agree"] and out["beats_dca"])


# ================= A5 hardening (QA regressions) =================

def test_nan_evidence_cannot_promote():
    """Allow-on-proof: NaN survives any refuse-comparison, so the gate must AFFIRM finiteness."""
    reg = StrategyRegistry(); reg.register(QualityMomentum())
    with pytest.raises(PromotionEvidenceError):
        reg.promote("quality_momentum", evidence={"base_rate": float("nan"), "n": 100})
    assert reg.get("quality_momentum").meta.mode == PromotionMode.BACKTEST


def test_live_rungs_are_founder_only_regardless_of_evidence():
    """No track record, however good, lets the agent promote ITSELF into real money."""
    reg = StrategyRegistry(); reg.register(QualityMomentum())
    ev = {"base_rate": 0.9, "n": 500}
    reg.promote("quality_momentum", evidence=ev)                 # → realistic_paper
    reg.promote("quality_momentum", evidence=ev)                 # → shadow
    with pytest.raises(PromotionEvidenceError, match="founder-only"):
        reg.promote("quality_momentum", evidence=ev)             # → live_small REFUSED
    assert reg.get("quality_momentum").meta.mode == PromotionMode.SHADOW
    assert reg.promote("quality_momentum", by_founder="Chiko") == PromotionMode.LIVE_SMALL

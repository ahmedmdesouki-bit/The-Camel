"""
S11a — strategy framework: registry, promotion ladder, the strategy-portfolio matrix, the starter
trio + dividend_growth, the mixer, and the dividend cash mechanics. All strategies are pure and only
ever PROPOSE compliant names (defence in depth — the Sharia gate still enforces downstream).
"""
from trader.strategies.base import StrategyContext, PromotionMode, StrategyStatus
from trader.strategies.registry import StrategyRegistry
from trader.strategies.mixer import StrategyMixer
from trader.strategies.core_dca import CoreDCA
from trader.strategies.quality_momentum import QualityMomentum, momentum_12_1
from trader.strategies.etf_rotation import ETFRegimeRotation, target_etf
from trader.strategies.dividend_growth import DividendGrowth, DividendProfile
from trader.strategies.dividends import net_dividend, purification_amount


def _ctx(**kw):
    base = dict(regime="DISINFLATION_GROWTH", whitelist={"SPUS": "pass", "AAPL": "pass", "HLAL": "pass"},
                cash_usd=1000.0)
    base.update(kw)
    return StrategyContext(**base)


# ---------------- starter strategies ----------------

def test_core_dca_always_proposes_the_core_etf():
    sigs = CoreDCA().generate_signals(_ctx())
    assert len(sigs) == 1 and sigs[0].symbol == "SPUS" and sigs[0].action == "buy"


def test_momentum_12_1_pure():
    up = [100.0 + k for k in range(300)]          # trending up
    assert momentum_12_1(up) > 0
    assert momentum_12_1([100.0] * 10) == 0.0     # not enough history → 0


def test_quality_momentum_proposes_only_trending_names():
    ctx = _ctx(closes={"AAPL": [100.0 + k for k in range(300)],     # strong uptrend
                       "SPUS": [200.0] * 300})                       # flat → no momentum
    sigs = QualityMomentum().generate_signals(ctx)
    assert [s.symbol for s in sigs] == ["AAPL"]


def test_etf_rotation_maps_regime_to_target_or_cash():
    assert target_etf("RECOVERY") == "SPUS"
    assert target_etf("INFLATION_SHOCK") == "MNZL"
    assert target_etf("GEOPOLITICAL_RISK_OFF") is None
    risk_off = ETFRegimeRotation().generate_signals(_ctx(regime="RECESSION_RISK"))
    assert risk_off[0].action == "hold" and risk_off[0].symbol == "CASH"   # steps aside


def test_dividend_growth_filters_payout_and_streak():
    cands = {"GOOD": DividendProfile("GOOD", payout_ratio=0.5, growth_streak_years=10),
             "HIGHPAYOUT": DividendProfile("HIGHPAYOUT", payout_ratio=0.9, growth_streak_years=10),
             "SHORTSTREAK": DividendProfile("SHORTSTREAK", payout_ratio=0.4, growth_streak_years=2)}
    ctx = _ctx(whitelist={"GOOD": "pass", "HIGHPAYOUT": "pass", "SHORTSTREAK": "pass"})
    s = DividendGrowth(cands)
    sigs = s._filter(s.generate_signals(ctx), ctx)
    assert [x.symbol for x in sigs] == ["GOOD"]


def test_strategy_never_proposes_non_compliant_name():
    # AAPL trends up but is NOT a Sharia pass in this context → strategy must not propose it
    ctx = _ctx(whitelist={"AAPL": "doubtful"}, closes={"AAPL": [100.0 + k for k in range(300)]})
    s = QualityMomentum()
    assert s._filter(s.generate_signals(ctx), ctx) == []


# ---------------- registry + promotion ladder ----------------

def test_registry_register_and_active():
    reg = StrategyRegistry()
    reg.register(CoreDCA()); reg.register(QualityMomentum())
    assert len(reg.active()) == 2
    reg.pause("quality_momentum")
    assert [s.meta.id for s in reg.active()] == ["core_dca"]


def test_promotion_ladder_one_rung_and_demote_to_cooldown():
    reg = StrategyRegistry(); reg.register(QualityMomentum())     # starts at backtest
    assert reg.promote("quality_momentum") == PromotionMode.REALISTIC_PAPER
    assert reg.promote("quality_momentum") == PromotionMode.SHADOW
    assert reg.demote("quality_momentum") == PromotionMode.REALISTIC_PAPER   # failure → cooldown, not deleted


def test_weight_only_within_band():
    reg = StrategyRegistry(); reg.register(CoreDCA())
    assert reg.set_weight("core_dca", 0.9, band=(0.0, 0.5)) == 0.5   # clamped to the band


def test_signals_for_respects_regime_and_portfolio_matrix():
    reg = StrategyRegistry()
    qm = QualityMomentum()
    qm.meta.allowed_portfolios = ["thematic_satellite"]
    reg.register(qm)
    ctx = _ctx(regime="DISINFLATION_GROWTH", closes={"AAPL": [100.0 + k for k in range(300)]})
    # allowed in its portfolio:
    assert reg.signals_for(ctx, portfolio_id="thematic_satellite")
    # forbidden elsewhere:
    assert reg.signals_for(ctx, portfolio_id="income_dividend") == []
    # wrong regime → silent:
    assert reg.signals_for(_ctx(regime="RECESSION_RISK",
                                closes={"AAPL": [100.0 + k for k in range(300)]}),
                           portfolio_id="thematic_satellite") == []


# ---------------- mixer ----------------

def test_mixer_blends_overlapping_buys():
    reg = StrategyRegistry(); reg.register(CoreDCA()); reg.register(ETFRegimeRotation())
    ctx = _ctx(regime="RECOVERY")
    sigs = reg.signals_for(ctx)                       # both propose SPUS
    blended = StrategyMixer().blend(sigs, reg)
    spus = next(c for c in blended if c.symbol == "SPUS")
    assert set(spus.strategies) == {"core_dca", "etf_regime_rotation"}   # convictions combined


# ---------------- dividend mechanics ----------------

def test_dividend_cash_split_nra():
    d = net_dividend(100.0, withholding_rate=0.15)
    assert d.gross == 100.0 and d.withheld == 15.0 and d.net == 85.0


def test_purification_amount():
    assert purification_amount(100.0, 0.03) == 3.0

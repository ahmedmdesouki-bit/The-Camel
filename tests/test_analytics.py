"""Quality/income analytics (Alaa-review backlog): yield-on-cost + moat matrix."""
from strategies.analytics import yield_on_cost, moat_score, MOAT_WEIGHTS


def test_yield_on_cost_uses_cost_basis_not_price():
    # bought at $40, $2/yr dividend → 5% yield-on-cost regardless of today's price
    assert yield_on_cost(2.0, 40.0) == 0.05


def test_yield_on_cost_guards_zero_cost():
    assert yield_on_cost(2.0, 0.0) == 0.0
    assert yield_on_cost(2.0, -5.0) == 0.0


def test_moat_weights_sum_to_one():
    assert round(sum(MOAT_WEIGHTS.values()), 6) == 1.0


def test_moat_all_strong_is_wide_100():
    a = moat_score({k: 1.0 for k in MOAT_WEIGHTS})
    assert a.score == 100.0 and a.band == "wide"


def test_moat_all_weak_is_none_zero():
    a = moat_score({})
    assert a.score == 0.0 and a.band == "none"


def test_moat_clamps_and_bands():
    a = moat_score({"gross_margin_stability": 5.0, "roic_above_wacc": 1.0})  # clamps to 1.0 each
    # 0.25*100 + 0.25*100 = 50 → narrow
    assert a.score == 50.0 and a.band == "narrow"

"""
S12a — realistic-paper execution: the fill/slippage model + corporate-action/dividend replay.

Locks in that realistic_paper does what broker paper does NOT: crosses the real spread, partial-fills
against displayed size, charges fees, REJECTS stale data (never fabricates a price), enforces whole
shares, and replays the 4-stage dividend pipeline + splits on the NRA-withholding frame.
"""
from trader.execution.models import Order, MarketSnapshot, FillStatus
from trader.execution.fill import simulate_fill, slippage_bps
from trader.execution.realistic_paper import RealisticPaperExecutor
from trader.execution.corporate_actions import announce, entitled_qty, settle, attribute, replay_split


def _snap(**kw):
    base = dict(symbol="SPUS", bid=99.0, ask=101.0, last=100.0, displayed_size=100,
                as_of="2026-06-07T15:00:00+00:00")
    base.update(kw)
    return MarketSnapshot(**base)


# ---------------- fill + slippage ----------------

def test_marketable_buy_fills_at_the_ask_with_fees():
    f = simulate_fill(Order("SPUS", "buy", 10, limit_price=101.0), _snap(),
                      now="2026-06-07T15:00:30+00:00")
    assert f.status == FillStatus.FILLED and f.fill_price == 101.0   # crosses the spread (pays ask)
    assert f.fees > 0 and f.slippage_bps == slippage_bps(_snap(), "buy")


def test_non_marketable_limit_is_no_fill_not_a_price():
    f = simulate_fill(Order("SPUS", "buy", 10, limit_price=100.0), _snap(),  # limit < ask
                      now="2026-06-07T15:00:30+00:00")
    assert f.status == FillStatus.NO_FILL and f.filled_qty == 0          # honest non-fill, no fabricated price


def test_stale_quote_is_rejected():
    f = simulate_fill(Order("SPUS", "buy", 10, limit_price=101.0), _snap(as_of="2026-06-07T15:00:00+00:00"),
                      now="2026-06-07T15:30:00+00:00", max_age_s=900)   # 30 min old > 15 min
    assert f.status == FillStatus.REJECTED and "stale" in f.reason


def test_market_order_refused_in_realistic_paper():
    f = simulate_fill(Order("SPUS", "buy", 10, limit_price=101.0, order_type="market"), _snap())
    assert f.status == FillStatus.REJECTED and "limit-orders only" in f.reason


def test_partial_fill_against_displayed_size():
    f = simulate_fill(Order("SPUS", "buy", 250, limit_price=101.0), _snap(displayed_size=100))
    assert f.status == FillStatus.PARTIAL and f.filled_qty == 100


def test_sell_fills_at_the_bid():
    f = simulate_fill(Order("SPUS", "sell", 5, limit_price=99.0), _snap())
    assert f.status == FillStatus.FILLED and f.fill_price == 99.0


def test_whole_share_constraint():
    ex = RealisticPaperExecutor(whole_shares=True)
    assert ex.execute(Order("SPUS", "buy", 10.5, limit_price=101.0), _snap()).status == FillStatus.REJECTED
    assert ex.execute(Order("SPUS", "buy", 10, limit_price=101.0), _snap()).status == FillStatus.FILLED


# ---------------- dividend 4-stage + splits ----------------

def test_dividend_announcement_flags_special():
    assert announce("X", 0.50, "2026-06-10", price=100.0).is_special is False     # 0.5% — ordinary
    assert announce("X", 30.0, "2026-06-10", price=100.0, pay_date="2026-06-20").is_special is True  # 30% special


def test_entitlement_requires_holding_before_ex_date():
    ann = announce("X", 1.0, "2026-06-10", price=100.0)
    assert entitled_qty(100, "2026-06-05", ann) == 100      # held before ex → entitled
    assert entitled_qty(100, "2026-06-10", ann) == 0        # bought on the ex-date → not entitled
    special = announce("X", 30.0, "2026-06-10", price=100.0, pay_date="2026-06-20")
    assert entitled_qty(100, "2026-06-15", special) == 100  # special: entitled through the pay date


def test_settlement_splits_gross_withheld_net_nra():
    ann = announce("X", 1.0, "2026-06-10")
    s = settle(ann, entitled=100, withholding_rate=0.15, impure_fraction=0.03)
    assert s.gross == 100.0 and s.withheld == 15.0 and s.net == 85.0   # NRA: gross→withheld→net separately
    assert s.purification == round(85.0 * 0.03, 6)


def test_attribution_decomposes_income_tax_price():
    ann = announce("X", 1.0, "2026-06-10")
    s = settle(ann, 100, withholding_rate=0.15)
    a = attribute(s, ex_date_price_drop=1.0, position_qty=100)
    assert a["income_effect"] == 85.0 and a["tax_effect"] == -15.0 and a["price_effect"] == -100.0


def test_split_replay_preserves_value():
    out = replay_split(qty=10, avg_cost=100.0, ratio=2.0)
    assert out["qty"] == 20 and out["avg_cost"] == 50.0     # 2:1 → value & basis unchanged

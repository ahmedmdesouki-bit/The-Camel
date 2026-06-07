"""
S9 slice 4 — in-house AAOIFI screen + multi-state Sharia cross-check.

Sharia is #1 in the priority hierarchy, so these tests lock the fail-safe behaviour:
the verified ratio thresholds, the disagreement→freeze rule, single-source→pending (a source can
fail but not clear a name), the authority stack, drift detection, and the error fail-safe.
"""
import json

from db.sqlite import connection
from sharia.aaoifi import AAOIFIFinancials, screen, compute_ratios, purification_ratio
from sharia.cross_check import (
    combine, apply_authority, detect_drift, run_sharia_cross_check,
    PASS, FAIL, DOUBTFUL, FROZEN, PENDING,
)
from sharia.whitelist import add_instrument, get_instrument


def _fin(symbol="AAPL", **kw):
    base = dict(avg_market_cap_12mo=1_000_000, total_debt=100_000, cash_and_deposits=50_000,
                interest_bearing_investments=50_000, receivables=100_000, total_assets=1_000_000,
                non_compliant_revenue=0, interest_income=10_000, total_revenue=1_000_000,
                sector="technology")
    base.update(kw)
    return AAOIFIFinancials(symbol=symbol, **base)


# ---------------- the verified AAOIFI screen (pure) ----------------

def test_clean_name_passes():
    r = screen(_fin())
    assert r.status == PASS and not r.breaches
    assert r.purification_ratio == 0.01            # interest_income 10k / revenue 1M


def test_each_ratio_breach_fails():
    assert screen(_fin(total_debt=400_000)).status == FAIL                    # 40% > 30%
    assert screen(_fin(cash_and_deposits=400_000, interest_bearing_investments=0)).status == FAIL
    assert screen(_fin(receivables=700_000, cash_and_deposits=50_000)).status == FAIL   # 75% > 67%
    assert screen(_fin(interest_income=60_000)).status == FAIL                # 6% > 5%
    bad = screen(_fin(total_debt=400_000))
    assert any("debt_ratio" in b for b in bad.breaches)


def test_prohibited_sector_excludes_regardless_of_ratios():
    r = screen(_fin(sector="gambling"))               # clean ratios, haram sector
    assert r.status == FAIL and r.sector_excluded


def test_doubtful_band_just_under_the_limit():
    r = screen(_fin(total_debt=290_000))              # 29% → within 2pp of 30% → doubtful
    assert r.status == DOUBTFUL and not r.breaches and r.near_misses


def test_missing_denominator_is_doubtful_not_pass():
    r = screen(_fin(avg_market_cap_12mo=0))           # can't compute debt/liquidity → never silently pass
    assert r.status == DOUBTFUL
    assert compute_ratios(_fin(avg_market_cap_12mo=0))["debt_ratio"] is None


def test_uses_12mo_avg_market_cap_denominator():
    # same debt, different 12-mo-avg mktcap → different ratio (proves the AAOIFI denominator is used)
    assert compute_ratios(_fin(total_debt=300_000, avg_market_cap_12mo=1_000_000))["debt_ratio"] == 0.3
    assert compute_ratios(_fin(total_debt=300_000, avg_market_cap_12mo=2_000_000))["debt_ratio"] == 0.15


# ---------------- multi-state combine / authority / drift (pure) ----------------

def test_combine_rules():
    assert combine(PASS, PASS)[0] == PASS
    assert combine(PASS, FAIL)[0] == FAIL and combine(FAIL, PASS)[0] == FAIL
    assert combine(PASS, DOUBTFUL)[0] == DOUBTFUL          # disagreement → doubtful (freeze)
    assert combine(PASS, None)[0] == PENDING               # single source can't CLEAR a name
    assert combine(FAIL, None)[0] == FAIL                  # but a single source CAN fail it


def test_authority_stack():
    assert apply_authority(PASS, local_board_status=FAIL) == (FAIL, "local_board")   # board overrides
    assert apply_authority(PASS, founder_action="freeze") == (FROZEN, "founder")     # founder tightens
    assert apply_authority(FAIL, founder_action="freeze")[0] == FAIL                 # cannot loosen a fail
    assert apply_authority(PASS) == (PASS, "AAOIFI")


def test_detect_drift():
    prev = {"debt_ratio": 0.20, "liquid_assets_ratio": 0.10}
    assert detect_drift(prev, {"debt_ratio": 0.27, "liquid_assets_ratio": 0.10}) is True   # crept to band
    assert detect_drift(prev, {"debt_ratio": 0.205, "liquid_assets_ratio": 0.10}) is False
    assert detect_drift(None, {"debt_ratio": 0.99}) is False                                # no prior


# ---------------- the fail-safe writer (end-to-end) ----------------

def _add(dbs, sym):
    add_instrument(dbs.sharia, sym, "stock", approved_by="chiko", scan_id="s1")


def test_pass_with_quorum_stays_compliant(dbs):
    _add(dbs, "AAPL")
    out = run_sharia_cross_check(dbs, lambda s: _fin(s), lambda s: PASS)
    assert out[0].final_status == PASS
    assert get_instrument(dbs.sharia, "AAPL")["frozen"] == 0
    assert get_instrument(dbs.sharia, "AAPL")["sharia_status"] == "compliant"
    with connection(dbs.sharia) as conn:
        row = conn.execute("SELECT * FROM sharia_status WHERE symbol='AAPL'").fetchone()
    assert row["final_status"] == PASS and json.loads(row["ratios"])["debt_ratio"] == 0.1


def test_disagreement_freezes_for_new_buys(dbs):
    _add(dbs, "AAPL")
    out = run_sharia_cross_check(dbs, lambda s: _fin(s), lambda s: DOUBTFUL)   # in-house pass × cc doubtful
    assert out[0].final_status == DOUBTFUL
    assert get_instrument(dbs.sharia, "AAPL")["frozen"] == 1                   # frozen for new buys


def test_single_source_pass_is_pending_not_frozen(dbs):
    _add(dbs, "AAPL")
    out = run_sharia_cross_check(dbs, lambda s: _fin(s), lambda s: None)       # no cross-check
    assert out[0].final_status == PENDING
    assert get_instrument(dbs.sharia, "AAPL")["frozen"] == 0                   # can hold/observe, not frozen
    assert get_instrument(dbs.sharia, "AAPL")["sharia_status"] == "pending_review"


def test_fail_freezes(dbs):
    _add(dbs, "BANKX")
    out = run_sharia_cross_check(dbs, lambda s: _fin(s, total_debt=500_000), lambda s: PASS)
    assert out[0].final_status == FAIL and get_instrument(dbs.sharia, "BANKX")["frozen"] == 1


def test_local_board_override_in_writer(dbs):
    _add(dbs, "AAPL")
    out = run_sharia_cross_check(dbs, lambda s: _fin(s), lambda s: PASS,
                                 local_board={"AAPL": FAIL})                   # local board says non-compliant
    assert out[0].final_status == FAIL and out[0].authority == "local_board"
    assert get_instrument(dbs.sharia, "AAPL")["frozen"] == 1


def test_financials_error_is_fail_safe(dbs):
    _add(dbs, "AAPL")
    def boom(_):
        raise ValueError("vendor down")
    out = run_sharia_cross_check(dbs, boom, lambda s: PASS)
    assert out[0].final_status == FROZEN                       # error → freeze, never trade through uncertainty
    assert get_instrument(dbs.sharia, "AAPL")["frozen"] == 1


def test_drift_flagged_across_screens(dbs):
    _add(dbs, "AAPL")
    run_sharia_cross_check(dbs, lambda s: _fin(s, total_debt=200_000), lambda s: PASS)   # 20%
    out = run_sharia_cross_check(dbs, lambda s: _fin(s, total_debt=270_000), lambda s: PASS)  # 27% → drift
    assert out[0].drift is True

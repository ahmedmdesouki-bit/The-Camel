"""
S11c — the 4-tier Learning Engine. L1 auto base-rate · L2 auto weight within band · L3 propose-only
(never auto-applies; L4 founder approves) · regime affinity gated at N≥20 · anomaly detector.
"""
from learning.base_rate_updater import update_base_rate
from learning.strategy_scorer import score_vs_expected, auto_weight
from learning.regime_matcher import learn_affinity
from learning.anomaly_detector import detect_underperformance
from learning.improvement_proposer import propose, list_pending, decide


# ---------------- L1 ----------------

def test_base_rate_moves_toward_evidence():
    # prior 0.5 (weight 10), 8 wins / 2 losses → posterior rises but is smoothed by the prior
    post = update_base_rate(0.5, 10, wins=8, losses=2)
    assert 0.5 < post < 0.8
    assert update_base_rate(0.5, 0, 0, 0) == 0.5     # no data → unchanged


# ---------------- L2 ----------------

def test_auto_weight_stays_within_band():
    band = (0.0, 0.30)
    up = auto_weight(0.28, score=1.5, band=band, step=0.05)
    assert up == 0.30                                 # clamped to the band ceiling
    down = auto_weight(0.02, score=0.5, band=band, step=0.05)
    assert down == 0.0                                # clamped to the floor
    assert score_vs_expected(0.06, 0.03) == 2.0


# ---------------- regime affinity ----------------

def test_regime_affinity_needs_min_samples():
    out = learn_affinity({"RECOVERY": [True] * 15,                       # too few → excluded
                          "INFLATION_SHOCK": [True] * 18 + [False] * 7})  # 25 → included
    assert "RECOVERY" not in out
    assert out["INFLATION_SHOCK"] == round(18 / 25, 3)


# ---------------- anomaly detector ----------------

def test_anomaly_flags_only_with_evidence():
    assert detect_underperformance(0.30, 0.55, n=30).flagged is True       # 25pp gap, big sample
    assert detect_underperformance(0.30, 0.55, n=5).flagged is False       # too few
    assert detect_underperformance(0.52, 0.55, n=30).flagged is False      # within tolerance


# ---------------- L3 propose-only ----------------

def test_proposals_are_propose_only_until_founder_decides(dbs):
    pid = propose(dbs, "deactivate", strategy_id="quality_momentum",
                  detail={"reason": "decayed"}, rationale="recent edge below base-rate")
    pending = list_pending(dbs)
    assert len(pending) == 1 and pending[0]["strategy_id"] == "quality_momentum"
    assert pending[0]["status"] == "pending"          # NOT auto-applied

    decide(dbs, pid, approve=True, decided_by="chiko")    # L4 founder approval
    assert list_pending(dbs) == []                    # no longer pending

"""4-tier Learning Engine (S11). L1 auto base-rate · L2 auto weight within band · L3 propose-only · L4 founder-only."""
from learning.base_rate_updater import update_base_rate
from learning.strategy_scorer import score_vs_expected, auto_weight
from learning.regime_matcher import learn_affinity, MIN_SAMPLES_PER_REGIME
from learning.anomaly_detector import detect_underperformance, AnomalyFlag
from learning.improvement_proposer import propose, list_pending, decide

__all__ = [
    "update_base_rate", "score_vs_expected", "auto_weight",
    "learn_affinity", "MIN_SAMPLES_PER_REGIME", "detect_underperformance", "AnomalyFlag",
    "propose", "list_pending", "decide",
]

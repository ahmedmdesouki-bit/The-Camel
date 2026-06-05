"""
S5 — Opportunity Router tests. Leans toward inaction; no Trader path without Edge Proof.
"""
import pytest
from operator_os.opportunity_router import RouterInputs, route, score


def test_safety_gap_routes_to_system_improvement():
    d = route(RouterInputs(safety_complete=False, edge_proven=True))
    assert d.recommended_path == "system_improvement"

def test_missing_data_routes_to_research():
    d = route(RouterInputs(data_available=False, edge_proven=True))
    assert d.recommended_path == "research"

def test_no_capital_routes_to_wait():
    d = route(RouterInputs(capital_available=False, edge_proven=True))
    assert d.recommended_path == "wait"

def test_no_edge_no_product_routes_to_wait():
    d = route(RouterInputs(edge_proven=False, product_evidence=False))
    assert d.recommended_path == "wait"

def test_cannot_recommend_trader_without_edge_proof():
    # all gates open, but edge not proven and no product case → never "trader"
    d = route(RouterInputs(edge_proven=False, product_evidence=False,
                           factors={k: 1.0 for k in
                                    ("expected_upside", "evidence_quality", "downside_risk")}))
    assert d.recommended_path != "trader"

def test_edge_proven_routes_to_trader():
    d = route(RouterInputs(edge_proven=True,
                           factors={"expected_upside": 1.0, "evidence_quality": 1.0,
                                    "downside_risk": 1.0, "sharia_clarity": 1.0}))
    assert d.recommended_path == "trader"

def test_product_only_routes_to_entrepreneur():
    d = route(RouterInputs(edge_proven=False, product_evidence=True))
    assert d.recommended_path == "entrepreneur"

def test_both_viable_low_conviction_prefers_entrepreneur():
    # both edge + product, but weak factors → conviction < 0.6 → entrepreneur (bounded downside)
    d = route(RouterInputs(edge_proven=True, product_evidence=True, factors={}))
    assert d.recommended_path == "entrepreneur"

def test_both_viable_high_conviction_prefers_trader():
    d = route(RouterInputs(edge_proven=True, product_evidence=True,
                           factors={k: 1.0 for k in
                                    ("expected_upside", "evidence_quality", "downside_risk",
                                     "sharia_clarity", "capital_required", "time_required",
                                     "strategic_learning")}))
    assert d.recommended_path == "trader"

def test_score_weights_sum_to_one():
    assert score({k: 1.0 for k in
                  ("expected_upside", "evidence_quality", "downside_risk", "sharia_clarity",
                   "capital_required", "time_required", "strategic_learning")}) == pytest.approx(1.0)

def test_score_missing_factor_is_zero():
    assert score({}) == 0.0

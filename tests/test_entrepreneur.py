"""
S7 — Entrepreneur Product Engine: 17-field Product Gate, Entrepreneur Constitution, build pipeline.
All deterministic; the agent's autonomous scope is code-generation only.
"""
import pytest

from entrepreneur.product_gate import (
    ProductThesis, evaluate_gate, lead_product_thesis, field_count,
)
from entrepreneur.constitution import (
    EntrepreneurConstitution, EntAction, EntActionType,
)
from entrepreneur.build_pipeline import BuildPipeline, Stage, PipelineError, PipelineContext


# ---------------- Product Gate (17 fields) ----------------

def test_there_are_17_fields():
    assert field_count() == 17

def test_empty_thesis_is_rejected_with_all_missing():
    r = evaluate_gate(ProductThesis())
    assert not r.passed and len(r.missing) >= 15

def test_lead_product_thesis_passes_the_gate():
    r = evaluate_gate(lead_product_thesis())
    assert r.passed and not r.missing and not r.reasons

def test_missing_one_field_fails():
    t = lead_product_thesis()
    t.success_metric = "   "
    r = evaluate_gate(t)
    assert not r.passed and "success_metric" in r.missing

def test_invalid_risk_rating_fails():
    t = lead_product_thesis()
    t.compliance_risk_rating = "extreme"
    r = evaluate_gate(t)
    assert not r.passed and any("compliance_risk_rating" in x for x in r.reasons)

def test_non_pass_sharia_fails():
    t = lead_product_thesis()
    t.sharia_compliance_check = "doubtful"
    r = evaluate_gate(t)
    assert not r.passed and any("sharia" in x.lower() for x in r.reasons)

def test_empty_customer_list_fails():
    t = lead_product_thesis()
    t.first_10_customers = []
    r = evaluate_gate(t)
    assert not r.passed and "first_10_customers" in r.missing


# ---------------- Entrepreneur Constitution ----------------

def _C():
    return EntrepreneurConstitution()

def test_build_is_code_gen_allowed():
    assert _C().evaluate(EntAction(EntActionType.BUILD, business_model="travel ops support")).allow

def test_haram_business_blocked():
    d = _C().evaluate(EntAction(EntActionType.BUILD, business_model="an online casino for tourists"))
    assert not d.allow and d.rule_hit == "haram_business"

def test_data_collect_needs_privacy_review():
    assert not _C().evaluate(EntAction(EntActionType.DATA_COLLECT)).allow
    assert _C().evaluate(EntAction(EntActionType.DATA_COLLECT, privacy_reviewed=True)).allow

def test_asset_use_needs_rights_check():
    assert not _C().evaluate(EntAction(EntActionType.ASSET_USE)).allow
    assert _C().evaluate(EntAction(EntActionType.ASSET_USE, rights_cleared=True)).allow

def test_spend_over_budget_blocked():
    over = EntAction(EntActionType.SPEND, notional_usd=100, budget_remaining_usd=50)
    assert _C().evaluate(over).rule_hit == "budget"
    ok = EntAction(EntActionType.SPEND, notional_usd=40, budget_remaining_usd=50)
    assert _C().evaluate(ok).allow

def test_launch_needs_founder_approval():
    assert _C().evaluate(EntAction(EntActionType.LAUNCH)).rule_hit == "launch_needs_approval"
    assert _C().evaluate(EntAction(EntActionType.LAUNCH, approval_id="founder-ok")).allow

def test_regulated_claims_need_approval():
    a = EntAction(EntActionType.PUBLISH_COPY, claims=["medical"], copy_text="cures jet lag")
    assert _C().evaluate(a).rule_hit == "unapproved_claim"
    a2 = EntAction(EntActionType.PUBLISH_COPY, claims=["medical"], copy_text="cures jet lag",
                   approval_id="founder-ok")
    assert _C().evaluate(a2).allow

def test_compliance_guarantee_wording_blocked():
    a = EntAction(EntActionType.PUBLISH_COPY, copy_text="Our app is 100% Sharia certified!")
    assert _C().evaluate(a).rule_hit == "prohibited_claim_wording"
    # even with approval, the overstated-certification wording is not allowed
    a2 = EntAction(EntActionType.PUBLISH_COPY, copy_text="officially certified by us",
                   approval_id="founder-ok")
    assert not _C().evaluate(a2).allow


# ---------------- Build pipeline ----------------

def test_cannot_start_pipeline_with_failing_thesis():
    with pytest.raises(PipelineError):
        BuildPipeline(ProductThesis())   # empty thesis fails the gate

def test_pipeline_advances_sequentially_no_skip():
    p = BuildPipeline(lead_product_thesis())
    assert p.stage == Stage.PRODUCT_THESIS
    p.advance()
    assert p.stage == Stage.PRD            # +1, never jumps ahead

def test_staging_requires_tests_passed():
    p = BuildPipeline(lead_product_thesis())
    for _ in range(5):                     # thesis -> ... -> TESTS
        p.advance()
    assert p.stage == Stage.TESTS
    with pytest.raises(PipelineError):
        p.advance(PipelineContext(tests_passed=False))
    p.advance(PipelineContext(tests_passed=True))
    assert p.stage == Stage.STAGING

def test_production_requires_founder_approval():
    p = BuildPipeline(lead_product_thesis())
    for _ in range(5):
        p.advance()
    p.advance(PipelineContext(tests_passed=True))   # STAGING
    p.advance(PipelineContext(tests_passed=True))   # APPROVAL
    assert p.stage == Stage.APPROVAL
    with pytest.raises(PipelineError):              # no approval → cannot go live
        p.advance(PipelineContext(approval_id=None))
    p.advance(PipelineContext(approval_id="founder-ok", business_model="travel ops support"))
    assert p.stage == Stage.PRODUCTION and p.is_live()

def test_production_blocked_for_haram_business_even_with_approval():
    p = BuildPipeline(lead_product_thesis())
    for _ in range(7):                     # advance to APPROVAL (no tests gate until STAGING)
        ctx = PipelineContext(tests_passed=True)
        p.advance(ctx)
    assert p.stage == Stage.APPROVAL
    with pytest.raises(PipelineError):
        p.advance(PipelineContext(approval_id="founder-ok", business_model="a gambling betting app"))

def test_full_happy_path_to_measure():
    p = BuildPipeline(lead_product_thesis())
    live = PipelineContext(tests_passed=True, approval_id="founder-ok",
                           business_model="travel ops support")
    while p.stage != Stage.MEASURE:
        p.advance(live)
    assert p.stage == Stage.MEASURE
    with pytest.raises(PipelineError):     # already at final stage
        p.advance(live)

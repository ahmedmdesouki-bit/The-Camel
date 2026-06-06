"""
Product Gate (S7) — the Entrepreneur analog of the Edge Proof gate.

No product gets built until a ProductThesis answers all 17 fields and passes a deterministic
check (every field present, a Sharia pass, a valid risk rating, a real customer list, and a
human-review requirement for generated outputs). Pure: no I/O, fully unit-testable.
"""
from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import List

_RISK_RATINGS = ("low", "medium", "high")
_SHARIA_PASS = ("pass", "compliant")


@dataclass
class ProductThesis:
    """The 17 fields that must be answered before any build."""
    problem_statement: str = ""
    target_customer: str = ""
    evidence_of_pain: str = ""
    competitor_check: str = ""
    monetization_hypothesis: str = ""
    mvp_scope: str = ""
    build_cost_usd: float = -1.0                       # >= 0 once estimated
    launch_risk: str = ""
    sharia_compliance_check: str = ""                  # pass | fail | doubtful | ...
    data_privacy_check: str = ""
    success_metric: str = ""
    distribution_channel: str = ""
    first_10_customers: List[str] = field(default_factory=list)
    willingness_to_pay_evidence: str = ""
    compliance_risk_rating: str = ""                   # low | medium | high
    data_retention_policy: str = ""
    human_review_requirement: str = ""                 # how generated outputs are human-reviewed


@dataclass
class GateResult:
    passed: bool
    missing: List[str] = field(default_factory=list)   # fields not answered
    reasons: List[str] = field(default_factory=list)   # other failures


# free-text fields that simply must be non-empty
_TEXT_FIELDS = (
    "problem_statement", "target_customer", "evidence_of_pain", "competitor_check",
    "monetization_hypothesis", "mvp_scope", "launch_risk", "data_privacy_check",
    "success_metric", "distribution_channel", "willingness_to_pay_evidence",
    "data_retention_policy", "human_review_requirement",
)


def evaluate_gate(thesis: ProductThesis) -> GateResult:
    """Deterministic 17-field gate. passed=True only if every field is answered and valid."""
    missing: List[str] = []
    reasons: List[str] = []

    for name in _TEXT_FIELDS:
        if not str(getattr(thesis, name) or "").strip():
            missing.append(name)

    # structured fields
    if thesis.build_cost_usd is None or thesis.build_cost_usd < 0:
        missing.append("build_cost_usd")
    if not thesis.first_10_customers:
        missing.append("first_10_customers")
    if not str(thesis.compliance_risk_rating or "").strip():
        missing.append("compliance_risk_rating")
    if not str(thesis.sharia_compliance_check or "").strip():
        missing.append("sharia_compliance_check")

    # validity checks (only meaningful once present)
    if thesis.compliance_risk_rating and thesis.compliance_risk_rating.lower() not in _RISK_RATINGS:
        reasons.append(f"compliance_risk_rating '{thesis.compliance_risk_rating}' not in {_RISK_RATINGS}")
    if (thesis.sharia_compliance_check
            and thesis.sharia_compliance_check.lower() not in _SHARIA_PASS):
        reasons.append(f"sharia_compliance_check is '{thesis.sharia_compliance_check}', not a pass")

    passed = not missing and not reasons
    return GateResult(passed=passed, missing=missing, reasons=reasons)


def field_count() -> int:
    """Number of gate fields (sanity: the famous 17)."""
    return len(fields(ProductThesis))


def lead_product_thesis() -> ProductThesis:
    """The validated lead candidate — Arabic complaint/SLA-response assistant for Saudi
    travel/hospitality operators (the founder works in travel-tech). Used as the worked example
    that proves the gate + pipeline end-to-end. Not a launch — a thesis."""
    return ProductThesis(
        problem_statement=("Saudi travel/hospitality operators get Arabic complaints across WhatsApp, "
                           "email, and booking platforms and miss SLA windows, hurting CSAT and ratings."),
        target_customer="Small-to-mid Saudi hotels, tour operators, and travel agencies (10–200 staff).",
        evidence_of_pain=("Founder's first-hand travel-tech experience; operators manually triage Arabic "
                          "complaints with no SLA tracking; visible 1-star 'no response' reviews."),
        competitor_check=("Generic helpdesks (Zendesk/Freshdesk) are weak on Arabic + Saudi context; no "
                         "SLA-aware Arabic complaint assistant tailored to KSA travel."),
        monetization_hypothesis="SaaS subscription per seat/property; tiered by complaint volume.",
        mvp_scope=("Arabic complaint intake → categorize → draft SLA-aware response (human-reviewed) → "
                  "track SLA timer. No autosend; agent drafts, human approves."),
        build_cost_usd=0.0,                            # Phase 0: own time + free tiers
        launch_risk="Low — internal/pilot use; no autonomous customer messaging; human approves every reply.",
        sharia_compliance_check="pass",                # halal business activity (travel ops support)
        data_privacy_check=("PII (guest complaints) minimized + encrypted; no resale; KSA data-residency "
                           "respected; retention limited."),
        success_metric="Median SLA response time down 50% in a 3-operator pilot; >=2 paying after pilot.",
        distribution_channel="Founder's travel-tech network + direct outreach to KSA operators.",
        first_10_customers=["pilot-hotel-1", "pilot-tour-op-2", "pilot-agency-3"],
        willingness_to_pay_evidence="Verbal LOIs from 2 pilot operators; comparable helpdesk spend exists.",
        compliance_risk_rating="medium",
        data_retention_policy="Complaints retained 12 months then purged; export/delete on request.",
        human_review_requirement="Every AI-drafted reply requires human approval before it is sent.",
    )

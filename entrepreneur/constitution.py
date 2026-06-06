"""
Entrepreneur Constitution (S7) — the deterministic gate for the product arm.

Separate from the Trader Constitution. Same philosophy: the LLM proposes, this disposes, and
there is no agent-callable override. The agent's autonomous scope is **code-generation only**:
writing code and opening issues is fine; anything that touches customers, money, data, third-party
assets, or public claims requires passing this gate and a founder approval.

Pure, side-effect-free `evaluate(action) -> EntDecision`. Reuses the Trader's haram-activity screen
so a haram product can never be built.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from guardrail.constitution import HARAM_TERMS


class EntActionType(str, Enum):
    BUILD = "BUILD"               # write code / open issues — autonomous (code-gen only)
    DATA_COLLECT = "DATA_COLLECT" # collect/store user data — needs a privacy review
    ASSET_USE = "ASSET_USE"       # use a third-party asset — needs a rights check
    SPEND = "SPEND"               # paid hosting / ads — needs budget approval
    LAUNCH = "LAUNCH"             # deploy to production — needs founder approval
    PUBLISH_COPY = "PUBLISH_COPY" # marketing / product copy — checked for claims + wording


# claim categories that may never be made autonomously (need human approval)
_REGULATED_CLAIMS = ("legal", "financial", "medical")

# wording that overstates compliance/certification — never allowed, approval or not
_BANNED_PHRASES = (
    "guaranteed compliant", "official compliance guarantee", "100% sharia certified",
    "guaranteed halal", "officially certified", "government approved", "guaranteed returns",
    "guaranteed profit", "fully compliant guarantee", "certified compliant",
)


@dataclass
class EntAction:
    type: EntActionType
    business_model: str = ""                 # screened for haram activity
    claims: List[str] = field(default_factory=list)   # claim categories in the copy/output
    copy_text: str = ""                      # marketing/product copy (PUBLISH_COPY)
    privacy_reviewed: bool = False           # DATA_COLLECT
    rights_cleared: bool = False             # ASSET_USE
    approval_id: Optional[str] = None        # founder approval (LAUNCH / regulated claims)
    notional_usd: float = 0.0                # SPEND
    budget_remaining_usd: float = 0.0        # SPEND


@dataclass
class EntDecision:
    allow: bool
    reason: str
    rule_hit: Optional[str] = None


class EntrepreneurConstitution:
    @staticmethod
    def _has_haram(text: str) -> bool:
        t = (text or "").lower()
        return any(term in t for term in HARAM_TERMS)

    @staticmethod
    def _banned_wording(text: str) -> Optional[str]:
        t = (text or "").lower()
        for p in _BANNED_PHRASES:
            if p in t:
                return p
        return None

    def evaluate(self, a: EntAction) -> EntDecision:
        try:
            t = EntActionType(a.type)
        except ValueError:
            return EntDecision(False, f"Unknown entrepreneur action: {a.type}", "unknown_action")

        # Haram activity is a hard wall for any product action that references a business model.
        if self._has_haram(a.business_model):
            return EntDecision(False, "Business model fails the Sharia activity screen.", "haram_business")

        # Regulated (legal/financial/medical) claims always need human approval.
        regulated = [c for c in a.claims if str(c).lower() in _REGULATED_CLAIMS]
        if regulated and not a.approval_id:
            return EntDecision(False, f"Claims {regulated} need human approval.", "unapproved_claim")

        if t == EntActionType.BUILD:
            # code-generation only — always allowed once the activity screen passes
            return EntDecision(True, "Build (code-gen) within bounds.")

        if t == EntActionType.DATA_COLLECT:
            if not a.privacy_reviewed:
                return EntDecision(False, "Data collection needs a privacy review.", "privacy_review_required")
            return EntDecision(True, "Data collection cleared by privacy review.")

        if t == EntActionType.ASSET_USE:
            if not a.rights_cleared:
                return EntDecision(False, "Third-party asset needs a rights check.", "rights_check_required")
            return EntDecision(True, "Asset use cleared by rights check.")

        if t == EntActionType.SPEND:
            if a.notional_usd > a.budget_remaining_usd:
                return EntDecision(False, "Spend exceeds entrepreneur budget.", "budget")
            return EntDecision(True, "Spend within budget.")

        if t == EntActionType.LAUNCH:
            if not a.approval_id:
                return EntDecision(False, "Production launch needs founder approval.", "launch_needs_approval")
            return EntDecision(True, "Launch approved by founder.")

        if t == EntActionType.PUBLISH_COPY:
            banned = self._banned_wording(a.copy_text)
            if banned:
                return EntDecision(False, f"Copy uses prohibited compliance wording: '{banned}'.",
                                   "prohibited_claim_wording")
            return EntDecision(True, "Copy within wording rules.")

        return EntDecision(False, "Unhandled entrepreneur action.", "unhandled")

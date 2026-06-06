"""
Build pipeline (S7) — the Entrepreneur product state machine.

thesis -> PRD -> build plan -> issues -> MVP -> tests -> staging -> approval -> production -> measure

Stages advance strictly one at a time (no skipping). Hard gates:
  - a pipeline cannot START without a ProductThesis that passes the 17-field gate,
  - STAGING cannot be entered until tests passed,
  - PRODUCTION cannot be entered without founder approval AND the Entrepreneur Constitution
    allowing the LAUNCH (no autonomous production deploy — ever).
Pure logic; the actual PRD/issue/deploy side effects are wired only when a real product ships.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from entrepreneur.product_gate import ProductThesis, evaluate_gate
from entrepreneur.constitution import (
    EntrepreneurConstitution, EntAction, EntActionType,
)


class Stage(str, Enum):
    PRODUCT_THESIS = "PRODUCT_THESIS"
    PRD = "PRD"
    BUILD_PLAN = "BUILD_PLAN"
    ISSUES = "ISSUES"
    MVP = "MVP"
    TESTS = "TESTS"
    STAGING = "STAGING"
    APPROVAL = "APPROVAL"
    PRODUCTION = "PRODUCTION"
    MEASURE = "MEASURE"


_ORDER = [
    Stage.PRODUCT_THESIS, Stage.PRD, Stage.BUILD_PLAN, Stage.ISSUES, Stage.MVP,
    Stage.TESTS, Stage.STAGING, Stage.APPROVAL, Stage.PRODUCTION, Stage.MEASURE,
]


class PipelineError(RuntimeError):
    """Raised on an illegal pipeline transition (skip, ungated entry, or completed pipeline)."""


@dataclass
class PipelineContext:
    tests_passed: bool = False
    approval_id: Optional[str] = None      # founder approval for the production launch
    business_model: str = ""               # carried into the LAUNCH constitution check


class BuildPipeline:
    """One product's journey through the staged pipeline."""

    def __init__(self, thesis: ProductThesis, constitution: Optional[EntrepreneurConstitution] = None):
        gate = evaluate_gate(thesis)
        if not gate.passed:
            raise PipelineError(
                "Cannot start a pipeline — product thesis fails the 17-field gate: "
                + ", ".join(gate.missing + gate.reasons)
            )
        self.thesis = thesis
        self.constitution = constitution or EntrepreneurConstitution()
        self.stage = Stage.PRODUCT_THESIS

    # ---- transition rules ----
    def can_advance(self, ctx: Optional[PipelineContext] = None) -> Tuple[bool, str]:
        ctx = ctx or PipelineContext()
        idx = _ORDER.index(self.stage)
        if idx >= len(_ORDER) - 1:
            return False, "pipeline already at the final stage (MEASURE)"
        nxt = _ORDER[idx + 1]

        if nxt == Stage.STAGING and not ctx.tests_passed:
            return False, "cannot enter STAGING until tests have passed"
        if nxt == Stage.PRODUCTION:
            d = self.constitution.evaluate(EntAction(
                type=EntActionType.LAUNCH, approval_id=ctx.approval_id,
                business_model=ctx.business_model,
            ))
            if not d.allow:
                return False, f"cannot enter PRODUCTION: {d.reason}"
        return True, "ok"

    def advance(self, ctx: Optional[PipelineContext] = None) -> Stage:
        ok, reason = self.can_advance(ctx)
        if not ok:
            raise PipelineError(reason)
        self.stage = _ORDER[_ORDER.index(self.stage) + 1]
        return self.stage

    def is_live(self) -> bool:
        return self.stage in (Stage.PRODUCTION, Stage.MEASURE)

"""
S17.4 — proposal self-check (Level 2): a deterministic coherence audit of an Opportunity-Board proposal
BEFORE it reaches the founder.

The board (S17.6) is built deterministically, so a coherent board is the *expected* output — which is
exactly why a self-check is worth having: it turns "the board is coherent" from an assumption into a
CHECKED INVARIANT that catches a bug in the builder, a stale/hand-edited row, or a future LLM-desk
proposal that doesn't obey the rules. Pure logic over the proposal's own fields (duck-typed, no imports
of the board), so it never depends on how the proposal was produced.

A CRITICAL issue means the proposal contradicts a hard rule (a buy with no edge, a non-compliant buy, an
edge claim with no evidence) -> `ok=False` -> the Kitchen should withhold/flag it. A WARN is a soft gap.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

_COMPLIANT = ("pass", "compliant")


@dataclass
class CheckIssue:
    severity: str        # "critical" | "warn"
    code: str
    message: str


@dataclass
class SelfCheckResult:
    ok: bool                                   # False iff any CRITICAL issue
    issues: List[CheckIssue] = field(default_factory=list)

    @property
    def critical(self) -> List[CheckIssue]:
        return [i for i in self.issues if i.severity == "critical"]


def check_proposal(p) -> SelfCheckResult:
    """Audit one proposal for internal coherence. Duck-typed: `p` only needs the board's attributes."""
    issues: List[CheckIssue] = []
    action = (getattr(p, "action", "") or "").lower()
    sharia = (getattr(p, "sharia_status", "") or "").lower()
    edge = bool(getattr(p, "edge_allowed", False))
    hit = float(getattr(p, "hit_rate", 0.0) or 0.0)
    n = int(getattr(p, "sample_size", 0) or 0)
    conf = float(getattr(p, "confidence", 0.0) or 0.0)
    reasons = getattr(p, "reason_chain", []) or []
    inval = getattr(p, "invalidation", "") or ""

    # HARD rules (a violation is a contradiction of the Constitution's intent — critical):
    if action == "buy" and not edge:
        issues.append(CheckIssue("critical", "buy_without_edge",
                                 "a BUY proposal must carry a proven edge (alpha needs evidence)"))
    if action in ("buy", "dca") and sharia not in _COMPLIANT:
        issues.append(CheckIssue("critical", "noncompliant_accumulation",
                                 f"a {action.upper()} must be Sharia-compliant (got {sharia!r})"))
    if edge and (n <= 0 or hit <= 0.0):
        issues.append(CheckIssue("critical", "edge_without_evidence",
                                 f"edge_allowed=True but no supporting evidence (hit_rate={hit}, n={n})"))
    if not (0.0 <= conf <= 1.0):
        issues.append(CheckIssue("critical", "confidence_out_of_range",
                                 f"confidence {conf} is outside [0, 1]"))

    # SOFT gaps (worth surfacing, not blocking):
    if action == "avoid" and sharia in _COMPLIANT:
        issues.append(CheckIssue("warn", "avoid_compliant_name",
                                 "AVOID on a Sharia-compliant name should explain the regime/edge reason"))
    if not reasons:
        issues.append(CheckIssue("warn", "no_reason_chain", "proposal carries no reason chain"))
    if action in ("buy", "dca") and not inval:
        issues.append(CheckIssue("warn", "no_invalidation", "an accumulation proposal has no invalidation"))

    return SelfCheckResult(ok=not any(i.severity == "critical" for i in issues), issues=issues)


def audit_board(board) -> dict:
    """Audit a whole board. Returns the per-symbol results + the list of INCOHERENT (critical) symbols —
    the Kitchen renders an incoherent proposal as flagged/withheld rather than actionable."""
    results = {getattr(p, "symbol", f"#{i}"): check_proposal(p) for i, p in enumerate(board)}
    incoherent = [sym for sym, r in results.items() if not r.ok]
    return {"checked": len(board), "incoherent": incoherent, "results": results}

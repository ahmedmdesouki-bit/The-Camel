"""
S21 — the SKEPTIC: structured, mandatory dissent against every Opportunity-Board proposal.

The consultant's best new idea, and it fits the trust-inversion exactly: every proposal should carry a
counterargument and an explicit invalidation list, so a compelling-looking idea is never adopted without
its strongest objection on the record. Deterministic for now (rule-based risk flags derived from the
proposal's own fields); an LLM SKEPTIC desk can deepen this later under the S17.2 cost cap. Pure +
duck-typed (reads the board proposal's attributes), so it never depends on how the proposal was produced
and adds no path to act.

`stance`: concur (no objection) | caution (proceed only with the invalidation watched) | oppose (the
objection outweighs the case). A 'buy' is never a clean concur — alpha always gets a caution.
"""
from __future__ import annotations

from typing import List

_COMPLIANT = ("pass", "compliant")
_RISK_OFF = ("RECESSION_RISK", "GEOPOLITICAL_RISK_OFF", "INFLATION_SHOCK")
_THIN_SAMPLE = 30          # below this, the edge evidence is thin


def dissent(p) -> dict:
    """Build the structured counterargument for one proposal (duck-typed: action/symbol/regime/
    sharia_status/edge_allowed/hit_rate/sample_size/confidence)."""
    action = (getattr(p, "action", "") or "").lower()
    symbol = getattr(p, "symbol", "?")
    regime = getattr(p, "regime", "") or ""
    sharia = (getattr(p, "sharia_status", "") or "").lower()
    edge = bool(getattr(p, "edge_allowed", False))
    hit = float(getattr(p, "hit_rate", 0.0) or 0.0)
    n = int(getattr(p, "sample_size", 0) or 0)
    risk_off = regime in _RISK_OFF

    risks: List[str] = []
    invalidation: List[str] = []

    if action == "buy":
        stance = "caution"                          # alpha is never a clean concur
        risks += ["the move may already be crowded / priced in",
                  "valuation expansion may have run ahead of fundamentals",
                  "the edge may be regime-dependent and decay out of sample"]
        invalidation += ["the Edge Proof verdict falls below threshold on re-test",
                         "sector/relative strength breaks down",
                         f"{symbol} fails its next Sharia re-screen"]
        if n < _THIN_SAMPLE:
            risks.append(f"thin evidence (sample n={n} < {_THIN_SAMPLE})")
            stance = "oppose"                        # thin-sample alpha: object until more evidence
        if hit and hit < 0.55:
            risks.append(f"modest hit-rate ({hit:.0%})")
        if risk_off:
            risks.append(f"opening risk INTO a risk-off regime ({regime})")
            stance = "oppose"
        summary = (f"{symbol}: the buy case rests on a proven edge — but alpha is the claim most often "
                   f"wrong. Proceed only small, only with the invalidation watched.")
    elif action == "dca":
        stance = "concur"                            # the humble default is the safe objection-free choice
        risks += ["opportunity cost / cash drag if a real edge exists elsewhere",
                  "the Sharia-compliant core is narrow (concentration in a few ETFs)"]
        invalidation += ["a strategy proves a real edge → redeploy from DCA to the edge",
                         "the core ETF fails its Sharia re-screen → freeze"]
        summary = (f"{symbol}: DCA into the compliant core is the honest no-edge default — the main "
                   f"objection is opportunity cost, not risk of ruin.")
    elif action == "avoid":
        stance = "concur"
        summary = f"{symbol}: correctly excluded ({sharia or 'not compliant'}) — no dissent."
    else:  # wait / unknown
        stance = "concur"
        summary = f"{symbol}: waiting is a position — no objection."

    # a non-compliant accumulation is an automatic OPPOSE regardless of the above (defence in depth)
    if action in ("buy", "dca") and sharia not in _COMPLIANT:
        stance = "oppose"
        risks.insert(0, f"NOT Sharia-clear ({sharia or 'unknown'}) — must not accumulate")

    return {"symbol": symbol, "action": action, "stance": stance, "summary": summary,
            "key_risks": risks, "invalidation_events": invalidation}


def audit_board_dissent(board) -> List[dict]:
    """A dissent record for every proposal on the board (highest-objection first: oppose → caution → concur)."""
    order = {"oppose": 0, "caution": 1, "concur": 2}
    return sorted((dissent(p) for p in board), key=lambda d: order.get(d["stance"], 3))

"""
Assembled operator loop (S10.5) — the §4 pipeline, strung together for real.

The components were all built and unit-tested in isolation (S3–S10), but `loop/runner.py` called the
Constitution directly and `loop/scheduler.py` ran no-op callbacks, so the upgraded loop was never
*assembled* at runtime — and the Edge-Proof gate (which lives in `capital/allocator.py`) was bypassed.
This module assembles them and closes that Phase-1 blocker:

    Observe (regime) → Opportunity Router → Edge Proof + Constitution (Allocator) → Budget Kernel →
    Human-Approval gate (phase-gated) → Act (paper) → Learn

The load-bearing invariant (tested): **a buy with no passing EdgeReport is rejected by the ASSEMBLED
loop**, because every consequential action is routed through `Allocator.request(...)` — not through
`Constitution.evaluate` directly. Order of authority is preserved: Edge → Constitution → Budget →
Approval → Act. Still paper, still Phase 0; nothing here enables live capital.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from guardrail.constitution import Action, ActionType, PortfolioState
from capital.allocator import Allocator
from capital.budget_kernel import BudgetKernel, BudgetState
from operator_os.opportunity_router import route, RouterInputs
from ops.kill_switch import is_halted

log = logging.getLogger(__name__)


@dataclass
class ActionOutcome:
    symbol: str
    stage: str                 # "edge_or_constitution" | "budget" | "approval" | "executed"
    approved: bool
    reason: str
    result: Optional[str] = None


@dataclass
class TickResult:
    halted: bool = False
    regime: Optional[str] = None
    regime_confidence: Optional[float] = None
    router_path: Optional[str] = None
    router_reason: str = ""
    outcomes: List[ActionOutcome] = field(default_factory=list)

    @property
    def executed(self) -> List[str]:
        return [o.symbol for o in self.outcomes if o.stage == "executed" and o.approved]


def _classify_regime(dbs: CamelDbs):
    """Best-effort regime read (S9). Never raises — empty macro data → UNKNOWN."""
    try:
        from trader.regime.features import build_features
        from trader.regime.classifier import classify
        return classify(build_features(dbs))
    except Exception as exc:                              # pragma: no cover - defensive
        log.warning("regime classify failed: %s", exc)
        return None


def _oplog(dbs: CamelDbs, event_type: str, detail: str) -> None:
    try:
        with connection(dbs.portfolio) as conn:
            conn.execute("INSERT INTO op_log (event_type, detail) VALUES (?,?)", (event_type, detail))
    except Exception:                                    # pragma: no cover - logging must never break the loop
        pass


class AssembledLoop:
    """One governed tick. Dependencies are injected so it is fully testable on paper."""

    def __init__(self, dbs: CamelDbs, *, allocator: Optional[Allocator] = None,
                 budget_kernel: Optional[BudgetKernel] = None,
                 budget_state: Optional[BudgetState] = None,
                 broker_execute: Optional[Callable[[Action], Any]] = None,
                 approval_fn: Optional[Callable[[Action], bool]] = None,
                 phase: int = 0):
        self.dbs = dbs
        self.allocator = allocator or Allocator()
        self.budget_kernel = budget_kernel
        self.budget_state = budget_state or BudgetState()
        self.broker_execute = broker_execute or (lambda a: "simulated_fill")
        # live phases need a human; default is to WITHHOLD approval (fail-safe) — paper Phase 0 needs none
        self.approval_fn = approval_fn or (lambda a: False)
        self.phase = phase

    def run_tick(self, candidates: List[Action], state: PortfolioState,
                 edge_reports: Optional[Dict[str, Any]] = None) -> TickResult:
        if is_halted():
            log.warning("Kill switch active — assembled tick skipped.")
            return TickResult(halted=True)
        edge_reports = edge_reports or {}

        # 1 Observe — classify the macro regime (S9)
        rr = _classify_regime(self.dbs)
        regime = rr.regime.value if rr else None
        result = TickResult(regime=regime, regime_confidence=(rr.confidence if rr else None))

        # 2 Opportunity Router — leans to Wait; cannot pick Trader without a proven edge
        edge_proven = any(getattr(edge_reports.get(getattr(a, "symbol", None)), "trade_allowed", False)
                          for a in candidates if a.type == ActionType.TRADE and a.side == "buy")
        decision = route(RouterInputs(safety_complete=True, data_available=True,
                                      capital_available=state.cash_usd > 0, edge_proven=edge_proven))
        result.router_path, result.router_reason = decision.recommended_path, decision.reason
        _oplog(self.dbs, "ROUTER", f"{decision.recommended_path}: {decision.reason}")
        if decision.recommended_path != "trader":
            return result                                # nothing to act on this tick

        # 3 Act — every action routed through the Allocator (Edge Proof + Constitution), then Budget,
        #         then the phase-gated Human-Approval gate. NEVER Constitution-direct.
        for action in candidates:
            sym = getattr(action, "symbol", "?")
            er = edge_reports.get(sym)

            alloc = self.allocator.request(action, state, edge_report=er)
            if not alloc.approved:
                result.outcomes.append(ActionOutcome(sym, "edge_or_constitution", False,
                                                     alloc.decision.reason))
                _oplog(self.dbs, "ACT", f"{sym} BLOCKED (edge/constitution): {alloc.decision.reason}")
                continue

            if self.budget_kernel is not None:
                bd = self.budget_kernel.check(action.notional_usd, self.budget_state)
                if not bd.allow:
                    result.outcomes.append(ActionOutcome(sym, "budget", False, bd.reason))
                    _oplog(self.dbs, "ACT", f"{sym} BLOCKED (budget): {bd.reason}")
                    continue

            if self.phase >= 1:                          # live phases require a human approval
                if not self.approval_fn(action):
                    result.outcomes.append(ActionOutcome(sym, "approval", False,
                                                         "awaiting human approval"))
                    _oplog(self.dbs, "ACT", f"{sym} PENDING human approval")
                    continue

            res = self.broker_execute(action)
            if self.budget_kernel is not None:
                self.budget_state.spent_today += action.notional_usd
            result.outcomes.append(ActionOutcome(sym, "executed", True, "executed", result=str(res)))
            _oplog(self.dbs, "ACT", f"{sym} EXECUTED ({res})")
            if er is not None:
                try:
                    from engine.edge_proof import FullEdgeReport, log_full_edge_report
                    if isinstance(er, FullEdgeReport):
                        log_full_edge_report(self.dbs, er)
                except Exception:                        # pragma: no cover
                    pass

        return result

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
    # symbol -> {"strategies": [...], "theme": ...}; set by the driver so the Measure step can
    # attribute an executed trade to the strategies that proposed it. (S16)
    candidate_meta: Dict[str, Any] = field(default_factory=dict)

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

    def run_exits(self, proposals: List[Any], state: PortfolioState) -> List[ActionOutcome]:
        """Execute governed, reduce-only exits (S16-A7) for the EXISTING book — independent of the
        opportunity router (managing held risk is not a new opportunity). Authority chain per sell:
        kill switch → Allocator (sells are Edge-exempt by design; the Constitution enforces whitelist,
        close-only-for-frozen, phantom-sell and oversell) → phase-gated human approval → broker.
        Sells consume NO budget (they free cash). `proposals` are ExitProposal-shaped (symbol, qty,
        notional_usd, rule, reason)."""
        if is_halted():
            log.warning("Kill switch active — exits skipped.")
            return []
        outcomes: List[ActionOutcome] = []
        for p in proposals:
            sym = getattr(p, "symbol", "?")
            action = Action(ActionType.TRADE, symbol=sym, side="sell",
                            notional_usd=float(getattr(p, "notional_usd", 0.0)), mode="paper")
            alloc = self.allocator.request(action, state)            # edge-exempt; Constitution decides
            if not alloc.approved:
                outcomes.append(ActionOutcome(sym, "edge_or_constitution", False, alloc.decision.reason))
                _oplog(self.dbs, "EXIT", f"{sym} BLOCKED ({p.rule}): {alloc.decision.reason}")
                continue
            if self.phase >= 1:                                      # live exits also need a human
                if not self.approval_fn(action):
                    outcomes.append(ActionOutcome(sym, "approval", False, "awaiting human approval"))
                    _oplog(self.dbs, "EXIT", f"{sym} PENDING human approval ({p.rule})")
                    continue
            try:
                res = self.broker_execute(action)
            except Exception as exc:                                 # a refused fill must not crash the tick
                outcomes.append(ActionOutcome(sym, "execute_error", False, f"broker refused fill: {exc}"))
                _oplog(self.dbs, "EXIT", f"{sym} EXECUTE FAILED ({p.rule}): {exc}")
                continue
            outcomes.append(ActionOutcome(sym, "executed", True, p.reason, result=str(res)))
            _oplog(self.dbs, "EXIT", f"{sym} CLOSED ({p.rule}): {p.reason} ({res})")
        return outcomes

    def run_dca(self, dca_actions: List[Action], state: PortfolioState) -> List[ActionOutcome]:
        """Execute edge-EXEMPT DCA buys into the compliant core (S17 — the No-Edge fallback).

        The honest default when NO candidate proves an edge but capital is idle: mechanical accumulation
        into the already-Sharia-screened, whitelisted core ETF. This is the benchmark itself, NOT an alpha
        bet — so it is edge-exempt (the Allocator is called with `require_edge=False`, exactly as reduce-only
        sells are). The edge-exemption is the ONLY relaxation: every other wall still stands, in order —
            kill switch → Allocator(require_edge=False; the Constitution still enforces whitelist,
            cash-buffer, concentration, illiquidity, kill switch) → Budget Kernel → phase-gated human
            Approval → broker.
        Router-independent (like exits): deploying idle cash into the core is the no-edge default, not a new
        opportunity the router must select. An ALPHA buy can never reach here — the driver only ever passes
        the core_dca target(s), never a rejected alpha candidate. Returns ActionOutcomes (stage 'executed'
        on a real fill)."""
        if is_halted():
            log.warning("Kill switch active — DCA skipped.")
            return []
        outcomes: List[ActionOutcome] = []
        for action in dca_actions:
            sym = getattr(action, "symbol", "?")
            # edge-EXEMPT by design: no edge_report, require_edge=False. The Constitution is still the wall.
            alloc = self.allocator.request(action, state, require_edge=False)
            if not alloc.approved:
                outcomes.append(ActionOutcome(sym, "edge_or_constitution", False, alloc.decision.reason))
                _oplog(self.dbs, "DCA", f"{sym} BLOCKED (constitution): {alloc.decision.reason}")
                continue
            if self.budget_kernel is not None:
                bd = self.budget_kernel.check(action.notional_usd, self.budget_state)
                if not bd.allow:
                    outcomes.append(ActionOutcome(sym, "budget", False, bd.reason))
                    _oplog(self.dbs, "DCA", f"{sym} BLOCKED (budget): {bd.reason}")
                    continue
            if self.phase >= 1:                          # live DCA still needs a human, every time
                if not self.approval_fn(action):
                    outcomes.append(ActionOutcome(sym, "approval", False, "awaiting human approval"))
                    _oplog(self.dbs, "DCA", f"{sym} PENDING human approval")
                    continue
            try:
                res = self.broker_execute(action)
            except Exception as exc:                     # a refused fill must not crash the tick
                outcomes.append(ActionOutcome(sym, "execute_error", False, f"broker refused fill: {exc}"))
                _oplog(self.dbs, "DCA", f"{sym} EXECUTE FAILED: {exc}")
                continue
            if self.budget_kernel is not None:
                self.budget_state.spent_today += action.notional_usd
            outcomes.append(ActionOutcome(sym, "executed", True,
                                          "no-edge DCA into the compliant core", result=str(res)))
            _oplog(self.dbs, "DCA", f"{sym} EXECUTED ({res})")
        return outcomes

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

            # Act. A broker may legitimately refuse at fill time (no validated price, duplicate
            # client-order-id, phantom-sell re-check). That must NOT crash the tick or count as a
            # fill — record it as an execute_error and move on. (S16)
            try:
                res = self.broker_execute(action)
            except Exception as exc:
                result.outcomes.append(ActionOutcome(sym, "execute_error", False,
                                                     f"broker refused fill: {exc}"))
                _oplog(self.dbs, "ACT", f"{sym} EXECUTE FAILED: {exc}")
                continue
            if self.budget_kernel is not None:
                self.budget_state.spent_today += action.notional_usd
            result.outcomes.append(ActionOutcome(sym, "executed", True, "executed", result=str(res)))
            _oplog(self.dbs, "ACT", f"{sym} EXECUTED ({res})")
            if er is not None:
                try:
                    from trader.engine.edge_proof import FullEdgeReport, log_full_edge_report
                    if isinstance(er, FullEdgeReport):
                        log_full_edge_report(self.dbs, er)
                except Exception:                        # pragma: no cover
                    pass

        return result

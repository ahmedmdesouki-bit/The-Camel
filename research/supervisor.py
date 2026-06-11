"""
S17.2 — the Supervisor: keep the workforce alive AND keep it from spending the founder into the ground.

Two jobs, both guardrails:

  1. RESILIENCE — a desk that errors is RETRIED up to `max_retries`; if it still fails it is QUARANTINED
     for the rest of the cycle (skipped) instead of being run again and again. One bad desk never stalls
     or floods the cycle. (Builds directly on Workforce.run_desk's per-desk isolation.)

  2. THE COST CAP (the "runaway bill" guardrail) — a HARD ceiling on cumulative token/API cost per cycle.
     Each desk run is charged via an injected `cost_fn` (deterministic desks cost ~0; an LLM desk reports
     its token spend). Before each desk, if the meter has reached the cap the cycle STOPS — no further
     desks run. This is the structural protection against an LLM-desk loop quietly running up a huge bill.

Pure orchestration over the existing Workforce — it adds NO path to act or move money. Cost is injected,
so the whole thing is deterministic and testable with no real API calls.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from db.paths import CamelDbs
from research.workforce import Workforce, DeskResult


@dataclass
class CostMeter:
    """A simple spend meter against a hard per-cycle cap."""
    cap_usd: float
    spent_usd: float = 0.0

    def remaining(self) -> float:
        return max(0.0, self.cap_usd - self.spent_usd)

    def at_cap(self) -> bool:
        return self.spent_usd >= self.cap_usd

    def charge(self, cost: float) -> None:
        self.spent_usd += max(0.0, float(cost or 0.0))


@dataclass
class SupervisorReport:
    results: List[DeskResult] = field(default_factory=list)
    spent_usd: float = 0.0
    cap_usd: float = 0.0
    quarantined: List[str] = field(default_factory=list)
    stopped_on_cost: bool = False

    @property
    def ran(self) -> List[str]:
        return [r.desk_id for r in self.results]


class Supervisor:
    """Runs a Workforce cycle with retry/quarantine + a hard cost cap."""

    def __init__(self, workforce: Workforce, *, cost_cap_usd: float = 1.0, max_retries: int = 1,
                 cost_fn: Optional[Callable[[DeskResult], float]] = None):
        self.wf = workforce
        self.cost_cap_usd = float(cost_cap_usd)
        self.max_retries = int(max_retries)
        # deterministic desks cost ~0; an LLM desk would report token spend (e.g. via r.metrics['cost_usd'])
        self.cost_fn = cost_fn or (lambda r: float((r.metrics or {}).get("cost_usd", 0.0)))
        self.quarantined: set = set()

    def _run_with_retry(self, dbs: CamelDbs, desk_id: str, ctx: Optional[Dict]) -> DeskResult:
        r = self.wf.run_desk(dbs, desk_id, ctx)
        attempts = 0
        while r.status == "error" and attempts < self.max_retries:
            attempts += 1
            r = self.wf.run_desk(dbs, desk_id, ctx)
        if r.status == "error":
            self.quarantined.add(desk_id)            # repeated failure → quarantine for the rest of the run
        return r

    def run_cycle(self, dbs: CamelDbs, ctx: Optional[Dict] = None,
                  order: Optional[List[str]] = None) -> SupervisorReport:
        meter = CostMeter(self.cost_cap_usd)
        report = SupervisorReport(cap_usd=self.cost_cap_usd)
        for did in (order or self.wf.desk_ids()):
            if did in self.quarantined:
                continue
            if meter.at_cap():                        # the runaway-bill guardrail: stop, do not run more
                report.stopped_on_cost = True
                break
            r = self._run_with_retry(dbs, did, ctx)
            report.results.append(r)
            meter.charge(self.cost_fn(r))
        report.spent_usd = round(meter.spent_usd, 6)
        report.quarantined = sorted(self.quarantined)
        return report

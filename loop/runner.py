"""
Hermes loop runner — Observe → Thesis → Choose → Act → Measure → Learn.

The Constitution gate fires inside Act (step 4) before any order is submitted.
All steps are persisted to the runs table for post-crash resume.
Kill switch is checked before the loop starts.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from guardrail.constitution import Constitution, PortfolioState
from loop.state import RunState, begin_run, finish_run, update_run
from ops.kill_switch import is_halted

log = logging.getLogger(__name__)

# Type aliases
_ObserveFn = Callable[[], Dict[str, Any]]
_ThesisFn = Callable[[Dict[str, Any]], List[Any]]
_ChooseFn = Callable[[List[Any]], List[Any]]
_PortfolioFn = Callable[[], PortfolioState]
_ExecuteFn = Callable[[Any, Any], Any]
_MeasureFn = Callable[[], Dict[str, Any]]
_LearnFn = Callable[[Dict[str, Any]], None]


def _noop_observe() -> Dict[str, Any]:
    return {}

def _noop_theses(obs: Dict[str, Any]) -> List[Any]:
    return []

def _noop_choose(theses: List[Any]) -> List[Any]:
    return theses

def _noop_portfolio() -> PortfolioState:
    return PortfolioState(fund_usd=0, cash_usd=0)

def _noop_execute(action: Any, decision: Any) -> None:
    return None

def _noop_measure() -> Dict[str, Any]:
    return {}

def _noop_learn(metrics: Dict[str, Any]) -> None:
    return None


@dataclass
class LoopConfig:
    db_path: str
    phase: int = 0
    observe: Optional[_ObserveFn] = None
    generate_theses: Optional[_ThesisFn] = None
    choose: Optional[_ChooseFn] = None
    get_portfolio_state: Optional[_PortfolioFn] = None
    execute_order: Optional[_ExecuteFn] = None
    measure: Optional[_MeasureFn] = None
    learn: Optional[_LearnFn] = None
    limits: Optional[Dict] = None

    def constitution(self) -> Constitution:
        return Constitution(self.limits)


class LoopRunner:
    def __init__(self, cfg: LoopConfig):
        self.cfg = cfg
        self.constitution = cfg.constitution()
        # resolve hooks (fall back to no-ops so an unconfigured runner still runs)
        self._observe = cfg.observe or _noop_observe
        self._theses = cfg.generate_theses or _noop_theses
        self._choose = cfg.choose or _noop_choose
        self._portfolio = cfg.get_portfolio_state or _noop_portfolio
        self._execute = cfg.execute_order or _noop_execute
        self._measure = cfg.measure or _noop_measure
        self._learn = cfg.learn or _noop_learn

    def run_once(self) -> RunState:
        if is_halted():
            log.warning("Kill switch is active — loop skipped.")
            state = RunState(phase=self.cfg.phase, outcome="halted")
            return state

        state = begin_run(self.cfg.db_path, self.cfg.phase)
        try:
            self._execute_loop(state)
        except Exception as exc:
            log.exception("Loop crashed")
            finish_run(self.cfg.db_path, state, outcome=f"error: {exc}")
        return state

    # ──────────────────────────────────────────────
    def _execute_loop(self, state: RunState) -> None:
        db = self.cfg.db_path

        # 1 Observe
        try:
            observations = self._observe()
            state.mark("observe", "ok", detail={"keys": list(observations.keys())})
        except Exception as exc:
            state.mark("observe", "error", error=str(exc))
            return finish_run(db, state, "error")
        update_run(db, state)

        # 2 Thesis
        try:
            theses = self._theses(observations)
            state.mark("thesis", "ok", detail={"count": len(theses)})
        except Exception as exc:
            state.mark("thesis", "error", error=str(exc))
            return finish_run(db, state, "error")
        update_run(db, state)

        # 3 Choose
        try:
            chosen = self._choose(theses)
            state.mark("choose", "ok", detail={"chosen": len(chosen)})
        except Exception as exc:
            state.mark("choose", "error", error=str(exc))
            return finish_run(db, state, "error")
        update_run(db, state)

        # 4 Act — Constitution gate
        portfolio = self._portfolio()
        acted: List[Dict] = []
        for action in chosen:
            decision = self.constitution.evaluate(action, portfolio)
            if decision.allow:
                result = self._execute(action, decision)
                acted.append({"symbol": getattr(action, "symbol", "?"),
                               "allowed": True, "result": str(result)})
            else:
                log.info("Guardrail blocked %s: %s", getattr(action, "symbol", "?"),
                         decision.reason)
                acted.append({"symbol": getattr(action, "symbol", "?"),
                               "allowed": False, "reason": decision.reason})
        state.mark("act", "ok", detail={"results": acted})
        update_run(db, state)

        # 5 Measure
        metrics: Dict[str, Any] = {}
        try:
            metrics = self._measure()
            state.mark("measure", "ok", detail=metrics)
        except Exception as exc:
            state.mark("measure", "error", error=str(exc))
        update_run(db, state)

        # 6 Learn
        try:
            self._learn(metrics)
            state.mark("learn", "ok")
        except Exception as exc:
            state.mark("learn", "error", error=str(exc))
        update_run(db, state)

        finish_run(db, state, "complete")

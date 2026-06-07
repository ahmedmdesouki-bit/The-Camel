"""
Portfolio Engine (S11) — many portfolios, strategy-per-portfolio, under one Camel Fund.

A **portfolio** is the risk-bearing object (mandate, benchmark, capital share, lifecycle phase, risk
budgets, assigned strategies); a **strategy** is the decision-bearing object. The engine:
  * holds the 6 seed portfolios + a lifecycle (incubate→qualify→pilot→scale→defend→retire),
  * allocates fund capital by target weight,
  * does **tolerance-band rebalancing** that emits *suggestions, never automatic live trades*
    (acceptance checklist: drift → rebalance suggestion, a human/the gates decide),
  * enforces 4-level risk budgets,
  * persists to the `portfolios` table.

Trust inversion unchanged: the engine sizes/ranks and *proposes*; every resulting action still passes
the assembled loop → Edge Proof → Constitution → Budget → Approval. Execution stays EOD-positional.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection


class PortfolioPhase(str, Enum):
    INCUBATE = "incubate"      # research/replay, 0 live
    QUALIFY = "qualify"        # realistic paper, 0 live
    PILOT = "pilot"            # real money, low notional
    SCALE = "scale"            # full operating mode
    DEFEND = "defend"          # risk contraction
    RETIRE = "retire"          # decommission


_FORWARD = [PortfolioPhase.INCUBATE, PortfolioPhase.QUALIFY, PortfolioPhase.PILOT, PortfolioPhase.SCALE]


@dataclass
class Portfolio:
    portfolio_id: str
    name: str
    mandate: str = ""
    phase: PortfolioPhase = PortfolioPhase.INCUBATE
    benchmark: str = "SPUS"
    target_weight: float = 0.0
    cash_min_pct: float = 0.05
    gross_exposure_limit_pct: float = 1.0
    max_drawdown_pct: float = 0.25
    turnover_budget_pct: float = 0.30
    assigned_strategies: List[str] = field(default_factory=list)
    sharia_policy_version: str = "AAOIFI-2026"

    def benchmarks(self) -> Dict[str, str]:
        """Multi-benchmark: policy (what it should resemble) · opportunity (cost of the Sharia
        constraint) · cash hurdle."""
        return {"policy": self.benchmark, "opportunity": "ACWI", "cash": "CASH"}


# ---- the 6 seed portfolios (target weights sum to 1.0) ----
SEED_PORTFOLIOS: List[Portfolio] = [
    Portfolio("core_sharia_growth", "Core Sharia Growth", "long-horizon compliant core",
              phase=PortfolioPhase.QUALIFY, benchmark="SPUS", target_weight=0.40,
              assigned_strategies=["core_dca", "etf_regime_rotation"]),
    Portfolio("income_dividend", "Income / Dividend", "Sharia-screened quality income",
              benchmark="SPUS", target_weight=0.20, assigned_strategies=["dividend_growth"]),
    Portfolio("thematic_satellite", "Thematic Satellite", "momentum / themes",
              benchmark="SPUS", target_weight=0.15, max_drawdown_pct=0.30,
              assigned_strategies=["quality_momentum"]),
    Portfolio("cash_waiting_room", "Cash Waiting Room", "idle cash / watchlist",
              benchmark="CASH", target_weight=0.15, cash_min_pct=1.0, gross_exposure_limit_pct=0.0,
              assigned_strategies=[]),
    Portfolio("experimental_paper", "Experimental Paper", "new strategies pre-promotion",
              phase=PortfolioPhase.INCUBATE, benchmark="SPUS", target_weight=0.05,
              assigned_strategies=[]),
    Portfolio("entrepreneur_camel", "Entrepreneur Camel", "product budget / revenue KPIs",
              benchmark="REVENUE", target_weight=0.05, assigned_strategies=[]),
]


# ---- pure helpers ----

def advance_phase(phase: PortfolioPhase) -> PortfolioPhase:
    """One rung up the qualification ladder (stops at SCALE). DEFEND/RETIRE are off-ramps."""
    if phase in _FORWARD and phase != PortfolioPhase.SCALE:
        return _FORWARD[_FORWARD.index(phase) + 1]
    return phase


def allocate(portfolios: List[Portfolio], total_fund: float) -> Dict[str, float]:
    return {p.portfolio_id: round(total_fund * p.target_weight, 2) for p in portfolios}


@dataclass
class RebalanceSuggestion:
    portfolio_id: str
    action: str          # "add" | "reduce"
    drift: float
    note: str = ""


def tolerance_band_rebalance(current_weights: Dict[str, float], target_weights: Dict[str, float],
                             band: float = 0.05) -> List[RebalanceSuggestion]:
    """Suggest a rebalance only when a weight drifts outside its band. SUGGESTIONS, not trades —
    they still flow through the gates. Tolerance-band is the default (cuts turnover vs calendar)."""
    out: List[RebalanceSuggestion] = []
    for pid, target in target_weights.items():
        drift = round(current_weights.get(pid, 0.0) - target, 4)
        if abs(drift) > band:
            out.append(RebalanceSuggestion(pid, "reduce" if drift > 0 else "add", drift,
                                           note=f"drift {drift:+.1%} outside ±{band:.0%} band"))
    return out


def check_risk_budget(p: Portfolio, *, gross_exposure_pct: float,
                      drawdown_pct: float = 0.0, max_sector_pct: Optional[float] = None,
                      sector_cap: float = 0.40) -> List[str]:
    """4-level risk-budget check at the portfolio level. Returns breach strings (empty = within budget)."""
    breaches: List[str] = []
    if gross_exposure_pct > p.gross_exposure_limit_pct + 1e-9:
        breaches.append(f"gross exposure {gross_exposure_pct:.0%} > limit {p.gross_exposure_limit_pct:.0%}")
    if drawdown_pct < -p.max_drawdown_pct - 1e-9:
        breaches.append(f"drawdown {drawdown_pct:.0%} worse than max {-p.max_drawdown_pct:.0%}")
    if max_sector_pct is not None and max_sector_pct > sector_cap + 1e-9:
        breaches.append(f"sector concentration {max_sector_pct:.0%} > cap {sector_cap:.0%}")
    return breaches


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class PortfolioManager:
    def __init__(self, portfolios: Optional[List[Portfolio]] = None):
        self._p: Dict[str, Portfolio] = {p.portfolio_id: p for p in (portfolios or [])}

    def register(self, p: Portfolio) -> None:
        self._p[p.portfolio_id] = p

    def get(self, pid: str) -> Optional[Portfolio]:
        return self._p.get(pid)

    def all(self) -> List[Portfolio]:
        return list(self._p.values())

    def total_weight(self) -> float:
        return round(sum(p.target_weight for p in self._p.values()), 6)

    def allocate(self, total_fund: float) -> Dict[str, float]:
        return allocate(self.all(), total_fund)

    def strategies_for(self, pid: str) -> List[str]:
        p = self.get(pid)
        return list(p.assigned_strategies) if p else []

    # ---- persistence ----
    def save(self, dbs: CamelDbs) -> None:
        now = _utcnow()
        with connection(dbs.portfolio) as conn:
            for p in self._p.values():
                conn.execute(
                    "INSERT INTO portfolios (portfolio_id, name, mandate, phase, benchmark, "
                    " target_weight, cash_min_pct, gross_exposure_limit_pct, max_drawdown_pct, "
                    " turnover_budget_pct, assigned_strategies, sharia_policy_version, updated_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(portfolio_id) DO UPDATE SET phase=excluded.phase, "
                    " target_weight=excluded.target_weight, assigned_strategies=excluded.assigned_strategies, "
                    " updated_at=excluded.updated_at",
                    (p.portfolio_id, p.name, p.mandate, p.phase.value, p.benchmark, p.target_weight,
                     p.cash_min_pct, p.gross_exposure_limit_pct, p.max_drawdown_pct, p.turnover_budget_pct,
                     json.dumps(p.assigned_strategies), p.sharia_policy_version, now),
                )

    @classmethod
    def load(cls, dbs: CamelDbs) -> "PortfolioManager":
        with connection(dbs.portfolio) as conn:
            rows = [dict(r) for r in conn.execute("SELECT * FROM portfolios ORDER BY portfolio_id")]
        ps = [Portfolio(
            portfolio_id=r["portfolio_id"], name=r["name"], mandate=r["mandate"],
            phase=PortfolioPhase(r["phase"]), benchmark=r["benchmark"], target_weight=r["target_weight"],
            cash_min_pct=r["cash_min_pct"], gross_exposure_limit_pct=r["gross_exposure_limit_pct"],
            max_drawdown_pct=r["max_drawdown_pct"], turnover_budget_pct=r["turnover_budget_pct"],
            assigned_strategies=json.loads(r["assigned_strategies"] or "[]"),
            sharia_policy_version=r["sharia_policy_version"]) for r in rows]
        return cls(ps)

    @classmethod
    def seed(cls, dbs: CamelDbs) -> "PortfolioManager":
        m = cls([Portfolio(**{**p.__dict__}) for p in SEED_PORTFOLIOS])
        m.save(dbs)
        return m

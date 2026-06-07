"""
Scheduled jobs (S10.5, Workstream B) — runnable entrypoints for the built-but-untriggered ops.

Before this, only the daily loop and the manual kill-switch had a `__main__`; the weekly safety job,
the heartbeat/dead-man, the dashboard render, and the founder brief had no scheduled trigger. This
module gives them real entrypoints (mirroring `loop/scheduler.py`) so Windows Task Scheduler can fire:

    python -m loop.jobs daily    # heartbeat + render the dashboard + send the founder brief
    python -m loop.jobs weekly   # kill-switch self-test + backup + reconcile

Each step is best-effort and isolated — one failing step records an error but never aborts the others
or crashes the scheduler. Read-only / paper; nothing here trades.
"""
from __future__ import annotations

import os
from typing import Dict, Optional

from db.paths import CamelDbs


def run_daily_ops(dbs: CamelDbs, *, mode: str = "paper", notifier=None,
                  dashboard_path: Optional[str] = None,
                  price_moves: Optional[Dict[str, float]] = None) -> dict:
    """Beat the heartbeat, render the read-only dashboard, and send the founder daily brief."""
    summary: dict = {"heartbeat": None, "dashboard": None, "brief_sent": None, "errors": {}}

    try:
        from ops.heartbeat import beat
        summary["heartbeat"] = beat(dbs.portfolio)
    except Exception as exc:
        summary["errors"]["heartbeat"] = str(exc)

    try:
        from dashboard.generate import write_dashboard
        if dashboard_path:
            summary["dashboard"] = write_dashboard(dbs, dashboard_path, mode=mode)
    except Exception as exc:
        summary["errors"]["dashboard"] = str(exc)

    try:
        from alerts.brief import send_founder_brief
        r = send_founder_brief(dbs, mode=mode, notifier=notifier, price_moves=price_moves)
        summary["brief_sent"] = r.sent
        summary["brief_preview"] = r.preview
    except Exception as exc:
        summary["errors"]["brief"] = str(exc)

    return summary


def _build_portfolio_state(dbs: CamelDbs):
    """Assemble the live PortfolioState from the governed books (cash from ledger, positions from the
    positions table, whitelist from camel_sharia). Read-only."""
    from guardrail.constitution import PortfolioState
    from sharia.whitelist import load_whitelist
    from broker.positions import all_positions
    from db.sqlite import connection

    cash = 0.0
    try:
        with connection(dbs.portfolio) as conn:
            row = conn.execute("SELECT balance_after FROM ledger ORDER BY id DESC LIMIT 1").fetchone()
            cash = float(row[0]) if row and row[0] is not None else 0.0
    except Exception:
        cash = 0.0
    positions = {p.symbol: p.market_value for p in all_positions(dbs.portfolio)}
    fund = cash + sum(positions.values())
    return PortfolioState(fund_usd=fund, cash_usd=cash, positions=positions,
                          whitelist=load_whitelist(dbs.sharia))


def _budget_kernel(L: dict, fund: float, notional: float):
    """Build a Budget Kernel from the founder-owned limits (P1-C). An explicit `budget:` block in
    limits.yaml wins; otherwise derive sane caps from the fund + position cap so the kernel is always
    PRESENT and binding (never silently skipped). For live, tighten via the yaml `budget:` block."""
    from capital.budget_kernel import BudgetKernel, BudgetLimits
    b = dict(L.get("budget") or {})
    pos_cap = float(L.get("max_position_pct", 0.20))
    per_action = float(b.get("max_per_action", max(notional, fund * pos_cap)))
    daily = float(b.get("max_daily_spend", max(fund, per_action * 3)))
    return BudgetKernel(BudgetLimits(
        total_fund=max(fund, 1.0),
        max_per_action=max(per_action, 1.0),
        max_daily_spend=daily,
        max_weekly_spend=float(b.get("max_weekly_spend", daily * 3)),
        max_monthly_spend=float(b.get("max_monthly_spend", daily * 10)),
    ))


def run_trading_tick(dbs: CamelDbs, *, symbols, config_path: str = "config/limits.yaml",
                     registry=None, notional_per_trade: float = 50.0,
                     approval_fn=None) -> dict:
    """The PRODUCTION post-close decision job — the Edge-gated *assembled* path (P1-C/D/E).

    Unlike the legacy `loop/scheduler.py` heartbeat (which has no Edge Proof gate), this wires the full
    trust-inverted stack and is the entrypoint a founder schedules:
      - Constitution from `config/limits.yaml` → **phase has one founder-owned source** (P1-D),
      - a **Budget Kernel is injected** so the budget gate is never skipped (P1-C),
      - the **AssembledLoop** runs the strategy driver (Edge Proof → Constitution → Budget → Approval → Act),
      - approval **withholds by default** (fail-safe) for any phase ≥ 1.
    Paper-by-default; nothing here flips a phase or moves real money.
    """
    import os
    from guardrail.constitution import Constitution
    from capital.allocator import Allocator
    from capital.budget_kernel import BudgetState
    from loop.assembled import AssembledLoop
    from loop.driver import run_strategy_tick
    from trader.strategies.registry import StrategyRegistry
    from trader.strategies.core_dca import CoreDCA
    from trader.strategies.quality_momentum import QualityMomentum
    from trader.strategies.dividend_growth import DividendGrowth

    constitution = Constitution.from_yaml(config_path) if os.path.exists(config_path) else Constitution()
    phase = int(constitution.L.get("phase", 0))            # single source of truth for phase (P1-D)

    state = _build_portfolio_state(dbs)
    budget = _budget_kernel(constitution.L, state.fund_usd, notional_per_trade)

    if registry is None:
        registry = StrategyRegistry()
        for s in (CoreDCA(), QualityMomentum(), DividendGrowth()):
            registry.register(s)

    loop = AssembledLoop(
        dbs, allocator=Allocator(constitution), budget_kernel=budget,
        budget_state=BudgetState(), phase=phase,
        approval_fn=approval_fn,                            # None → withhold by default (fail-safe)
    )
    tick = run_strategy_tick(dbs, registry, state, symbols=list(symbols),
                             loop=loop, notional_per_trade=notional_per_trade)
    return {
        "phase": phase, "regime": tick.regime, "router_path": tick.router_path,
        "executed": tick.executed,
        "budget_present": True, "fund_usd": state.fund_usd, "cash_usd": state.cash_usd,
    }


def run_weekly_safety(dbs: CamelDbs, backup_dir: str) -> dict:
    """Run the weekly safety routine: kill-switch self-test + backup + reconcile."""
    try:
        from ops.scheduled_checks import run_weekly_checks
        res = run_weekly_checks(dbs, backup_dir)
        return {"ok": True, "result": str(res)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main(argv=None) -> int:                              # pragma: no cover - CLI entrypoint
    import argparse
    p = argparse.ArgumentParser(description="The Camel — scheduled ops jobs")
    p.add_argument("job", choices=["daily", "weekly", "tick"])
    p.add_argument("--db-dir", default=os.environ.get("CAMEL_DB_DIR", "."))
    p.add_argument("--dashboard", default=os.environ.get("CAMEL_DASHBOARD_PATH"))
    p.add_argument("--backup-dir", default=os.environ.get("CAMEL_BACKUP_DIR", "./backups"))
    p.add_argument("--config", default=os.environ.get("CAMEL_CONFIG", "config/limits.yaml"))
    p.add_argument("--symbols", default=os.environ.get("CAMEL_SYMBOLS", ""),
                   help="comma-separated symbols for the trading tick")
    args = p.parse_args(argv)

    dbs = CamelDbs.from_dir(args.db_dir)
    if args.job == "daily":
        print(run_daily_ops(dbs, dashboard_path=args.dashboard))
    elif args.job == "tick":
        syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
        print(run_trading_tick(dbs, symbols=syms, config_path=args.config))
    else:
        print(run_weekly_safety(dbs, args.backup_dir))
    return 0


if __name__ == "__main__":                               # pragma: no cover
    raise SystemExit(main())

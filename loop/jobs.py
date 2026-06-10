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

    # S16-A4 — the quarterly re-screen schedule, surfaced daily: whitelist names never re-screened or
    # past next_review_at. Reporting only — clearing a name takes an actual quorum-bound re-screen.
    try:
        from sharia.universe import rescreen_due
        summary["sharia_rescreen_due"] = rescreen_due(dbs)
    except Exception as exc:
        summary["errors"]["sharia_rescreen"] = str(exc)

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


def _apply_mtm(state, marks: dict) -> None:
    """Mark positions to market AND resync fund_usd = cash + Σ positions (S16 QA fix).

    Marking position values without recomputing the fund total hands the Constitution an internally
    inconsistent state: a depreciated book overstates fund_usd → the 20% concentration cap loosens;
    an appreciated book understates it → the tiered cash buffer loosens. Both rails drift fail-open
    by the marks-vs-fills gap. This keeps the invariant cash + Σ positions == fund on every leg."""
    for sym, mv in marks.items():
        if sym in state.positions:
            state.positions[sym] = mv
    state.fund_usd = state.cash_usd + sum(state.positions.values())


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


def ensure_opening_balance(dbs: CamelDbs, amount: float) -> bool:
    """Seed a one-time PAPER opening cash balance (a DEPOSIT) iff the ledger is empty. Returns True if it
    wrote one. The paper book needs an opening balance before the router will route to 'trader' (it
    requires cash_available); the *amount* is a founder choice, never auto-injected. Paper only."""
    if amount is None or amount <= 0:
        return False
    from db.sqlite import connection
    from ledger.writer import append_entry, _ensure_table as _ensure_ledger_table
    _ensure_ledger_table(dbs.portfolio)
    with connection(dbs.portfolio) as conn:
        row = conn.execute("SELECT 1 FROM ledger LIMIT 1").fetchone()
    if row is not None:
        return False                                        # never double-deposit
    append_entry(dbs.portfolio, "DEPOSIT", "", float(amount), ref="paper_opening_balance")
    return True


def run_trading_tick(dbs: CamelDbs, *, symbols, config_path: str = "config/limits.yaml",
                     registry=None, notional_per_trade: float = 50.0,
                     approval_fn=None, broker=None, learn: bool = True) -> dict:
    """The PRODUCTION post-close decision job — the FULL §4 loop, strung together (P1-C/D/E + S16).

    Unlike the legacy `loop/scheduler.py` heartbeat (which has no Edge Proof gate), this wires the full
    trust-inverted stack and is the entrypoint a founder schedules:
      - Constitution from `config/limits.yaml` → **phase has one founder-owned source** (P1-D),
      - a **Budget Kernel is injected** so the budget gate is never skipped (P1-C),
      - the **AssembledLoop** runs the strategy driver (Edge Proof → Constitution → Budget → Approval → Act),
      - approval **withholds by default** (fail-safe) for any phase ≥ 1,
      - **Act is durable (S16):** a real `PaperBroker` fills → orders + ledger + positions in one txn,
      - **the run is persisted (S16):** begin/finish a `runs` row so the ≥28-run live-readiness clock advances,
      - **Measure → Learn (S16):** executed trades are recorded to the learning ledger, round-tripped trades
        are resolved into win/loss, per-strategy base-rates are updated (L1), and systematic underperformance
        files an L3 **propose-only** request — closing the loop's previously-open back half.
    Paper-by-default; nothing here flips a phase or moves real money.
    """
    import os
    from guardrail.constitution import Constitution, Decision
    from capital.allocator import Allocator
    from capital.budget_kernel import BudgetState
    from loop.assembled import AssembledLoop
    from loop.driver import run_strategy_tick
    from loop.state import begin_run, finish_run
    from broker.paper import PaperBroker
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

    # S16 — a real paper broker so "Act" is durable (orders + ledger + positions in one txn). The loop
    # only calls this AFTER Edge Proof + Constitution + Budget + (phase-gated) Approval have passed, so the
    # decision the broker receives is allow=True by construction; submit() re-asserts it defensively.
    broker = broker or PaperBroker(dbs.portfolio, dbs.market)

    def _execute(action):
        return broker.submit(action, Decision(
            allow=True, reason="approved by assembled loop (Edge+Constitution+Budget+Approval)"))

    # S16 — persist a run row (the ≥28-run live-readiness clock can only advance if the tick records runs).
    # The whole governed body is wrapped: if anything raises (regime classify, strategy signals, the driver's
    # phase≥1 non-enforcing refusal, …) the run is finished as 'error' and NEVER left stuck 'running'.
    run = begin_run(dbs.portfolio, phase=phase)
    learn_summary: dict = {"resolved": 0, "strategies_updated": [], "proposals": []}
    try:
        loop = AssembledLoop(
            dbs, allocator=Allocator(constitution), budget_kernel=budget,
            budget_state=BudgetState(), phase=phase,
            broker_execute=_execute,                        # S16: durable paper Act
            approval_fn=approval_fn,                         # None → withhold by default (fail-safe)
        )

        # S16-A7 — manage the EXISTING book first: governed reduce-only exits run BEFORE any new buy
        # (free the cash, enforce invalidations, de-risk frozen names). Failure handling is LOUD via
        # two distinct paths: a broken reader/rule RAISES (→ the outer handler grades the run 'error'),
        # and a broker-refused exit fill is detected below and ALSO grades the run 'error' — risk
        # management never fails silently. Closes created here feed Measure→Learn this same tick.
        from trader.execution.exits import build_exit_proposals
        proposals, mtm, skipped_no_price = build_exit_proposals(dbs, state.whitelist, limits=constitution.L)
        _apply_mtm(state, mtm)                              # mark positions to market AND resync fund_usd
                                                            # (marks without a fund resync skew the
                                                            # concentration + cash-buffer rails — QA)
        exit_outcomes = loop.run_exits(proposals, state) if proposals else []
        exits_executed = [o.symbol for o in exit_outcomes if o.stage == "executed" and o.approved]
        exits_blocked = [(o.symbol, o.reason) for o in exit_outcomes
                         if o.stage == "edge_or_constitution"]
        exit_errors = [(o.symbol, o.reason) for o in exit_outcomes if o.stage == "execute_error"]
        if exit_errors:
            # A de-risking order that the broker REFUSED is a risk-management failure — grade the run
            # 'error' (non-counting) and do NOT proceed to add new risk on top of a broken exit path.
            run.mark("act", "error", error=f"exit fills refused: {exit_errors}")
            finish_run(dbs.portfolio, run, "error")
            return {"phase": phase, "regime": None, "router_path": None, "executed": [],
                    "exits": exits_executed, "exits_blocked": exits_blocked, "exit_errors": exit_errors,
                    "exit_skipped_no_price": skipped_no_price, "outcome": "error",
                    "budget_present": True, "fund_usd": state.fund_usd, "cash_usd": state.cash_usd,
                    "run_id": run.run_id, "learning": learn_summary}
        if exits_executed:
            state = _build_portfolio_state(dbs)             # cash/positions changed → rebuild,
            _apply_mtm(state, {s: v for s, v in mtm.items()  # then re-mark what remains open
                               if s in state.positions})

        # a symbol exited THIS tick is not a buy candidate THIS tick — no same-tick churn, and the
        # Measure baseline for the closed round-trip stays unambiguous (QA finding)
        buy_symbols = [s for s in symbols if s not in set(exits_executed)]
        tick = run_strategy_tick(dbs, registry, state, symbols=buy_symbols,
                                 loop=loop, notional_per_trade=notional_per_trade)

        # Did the Act stage actually DO anything? Only real fills count — an executed buy or an
        # executed exit. A routed-but-fully-blocked buy leg (e.g. phase≥1 approval withheld on every
        # candidate) is governed *deciding*, not governed *acting*, and must not advance the ≥28-run
        # readiness clock. (QA: router_path=='trader' alone over-counted.)
        acted = (not tick.halted) and (bool(tick.executed) or bool(exits_executed))
        run.mark("observe", "skipped" if tick.halted else "ok", tick.regime)
        run.mark("choose", "skipped" if tick.halted else "ok", tick.router_path)
        run.mark("act", "ok" if acted else "skipped",
                 {"executed": tick.executed, "exits": exits_executed,
                  "exits_blocked": exits_blocked, "exit_skipped_no_price": skipped_no_price})

        # S16 — Measure → Learn (best-effort: learning must never crash a governed tick; system integrity
        # ranks above learning speed). Skipped when halted — the kill switch means *do nothing*.
        if learn and not tick.halted:
            try:
                from learning.measure import record_trade_decision, resolve_and_learn
                for sym in tick.executed:                   # Measure: record each executed trade
                    meta = (tick.candidate_meta or {}).get(sym, {})
                    record_trade_decision(dbs, sym, meta.get("strategies", []))
                learn_summary = resolve_and_learn(dbs, registry=registry)   # Measure(resolve) + Learn
                run.mark("measure", "ok", {"recorded": len(tick.executed),
                                           "resolved": learn_summary["resolved"]})
                run.mark("learn", "ok", {"strategies_updated": len(learn_summary["strategies_updated"]),
                                         "proposals": len(learn_summary["proposals"])})
            except Exception as exc:                        # pragma: no cover - defensive
                run.mark("measure", "error", error=str(exc))
                run.mark("learn", "skipped", "measure failed")
        else:
            run.mark("measure", "skipped")
            run.mark("learn", "skipped")

        # Only a tick that did REAL governed work counts toward the ≥28-run live-readiness gate
        # (ops/live_readiness counts outcome LIKE 'complete%'). A halted tick (kill switch) or a pure
        # 'wait' (no buy leg AND no exits — e.g. unfunded book / no proven edge) gets a distinct,
        # NON-counting outcome, so the autonomy clock can never be advanced by no-op ticks. (S16)
        outcome = "halted" if tick.halted else ("complete" if acted else "no_action")
        finish_run(dbs.portfolio, run, outcome)
    except Exception:
        finish_run(dbs.portfolio, run, "error")             # never leave a runs row stuck 'running'
        raise

    return {
        "phase": phase, "regime": tick.regime, "router_path": tick.router_path,
        "executed": tick.executed, "exits": exits_executed, "outcome": outcome,
        "budget_present": True, "fund_usd": state.fund_usd, "cash_usd": state.cash_usd,
        "run_id": run.run_id, "learning": learn_summary,
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
    p.add_argument("--open-cash", type=float,
                   default=float(os.environ.get("CAMEL_PAPER_OPENING_CASH", "0") or 0),
                   help="one-time PAPER opening cash balance (DEPOSIT) if the ledger is empty; 0 = none")
    args = p.parse_args(argv)

    from db.paths import init_all
    dbs = CamelDbs.from_dir(args.db_dir)
    init_all(dbs)                                       # ensure all 7 schemas exist (idempotent) — the
                                                        # tick reads the `positions`/`ledger` tables, so a
                                                        # first run on an empty dir must create them first
    if args.job == "daily":
        print(run_daily_ops(dbs, dashboard_path=args.dashboard))
    elif args.job == "tick":
        syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
        if ensure_opening_balance(dbs, args.open_cash):
            print(f"seeded paper opening balance: ${args.open_cash:,.2f}")
        print(run_trading_tick(dbs, symbols=syms, config_path=args.config))
    else:
        print(run_weekly_safety(dbs, args.backup_dir))
    return 0


if __name__ == "__main__":                               # pragma: no cover
    raise SystemExit(main())

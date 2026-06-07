"""
Windows Task Scheduler entrypoint — a PAPER, NO-EXECUTE post-close heartbeat (Phase 0 only).

⚠️ SCOPE / SAFETY: this entrypoint runs the legacy `LoopRunner`, which evaluates the Constitution but does
**NOT** run the 17-check Edge Proof gate (that invariant lives on the *assembled* path:
`loop/driver.py::run_strategy_tick` → `loop/assembled.py::AssembledLoop`). It is wired with `fund=cash=0` and
the default no-op executor, so it executes nothing. To prevent it ever becoming a live execution path, it
**refuses to run at phase ≥ 1** — going live must use the assembled driver / `loop/jobs.py`, not this file.

Usage:
    python loop/scheduler.py

Environment variables:
    CAMEL_DB_DIR   directory that holds all seven camel_*.db files
                  (default: repo root)
    CAMEL_PHASE    0 (paper only — this entrypoint refuses ≥ 1; default: 0)
"""
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("camel.scheduler")


def main() -> None:
    db_dir = os.environ.get(
        "CAMEL_DB_DIR",
        str(Path(__file__).resolve().parent.parent),
    )
    phase = int(os.environ.get("CAMEL_PHASE", "0"))
    log.info("Scheduler fired. phase=%d db_dir=%s", phase, db_dir)

    # Fail-safe: this legacy heartbeat does NOT run the Edge Proof gate, so it must never be the live
    # execution path. Refuse phase >= 1 — going live uses loop/driver.py (run_strategy_tick) + loop/jobs.py.
    if phase >= 1:
        log.error("scheduler.py is a PAPER-only heartbeat (no Edge Proof gate); refusing phase=%d. "
                  "Use the assembled driver (loop/driver.py / loop/jobs.py) for any live phase.", phase)
        sys.exit(2)

    from db.paths import CamelDbs, init_all
    dbs = CamelDbs.from_dir(db_dir)
    init_all(dbs)

    from loop.runner import LoopConfig, LoopRunner
    from sharia.whitelist import load_whitelist
    from guardrail.constitution import PortfolioState

    def get_portfolio() -> PortfolioState:
        return PortfolioState(
            fund_usd=0, cash_usd=0,
            whitelist=load_whitelist(dbs.sharia),
        )

    cfg = LoopConfig(
        dbs=dbs,
        phase=phase,
        get_portfolio_state=get_portfolio,
    )
    state = LoopRunner(cfg).run_once()
    log.info("Loop finished: outcome=%s run_id=%s", state.outcome, state.run_id)
    sys.exit(0 if state.outcome == "complete" else 1)


if __name__ == "__main__":
    main()

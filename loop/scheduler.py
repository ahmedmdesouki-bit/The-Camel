"""
Windows Task Scheduler entrypoint.
Runs the paper loop once post-market-close (configure Task Scheduler to fire ~4:30pm ET).

Usage:
    python loop/scheduler.py

Environment variables (set in Task Scheduler or .env):
    NOAH_DB     path to local SQLite DB  (default: noah.db in repo root)
    NOAH_PHASE  0 | 1 | 2 | 3            (default: 0)
"""
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("noah.scheduler")


def main() -> None:
    db_path = os.environ.get(
        "NOAH_DB",
        str(Path(__file__).resolve().parent.parent / "noah.db"),
    )
    phase = int(os.environ.get("NOAH_PHASE", "0"))
    log.info("Scheduler fired. phase=%d db=%s", phase, db_path)

    from db.sqlite import init_db
    init_db(db_path)

    from loop.runner import LoopConfig, LoopRunner
    from sharia.whitelist import load_whitelist
    from guardrail.constitution import PortfolioState

    def get_portfolio() -> PortfolioState:
        return PortfolioState(
            fund_usd=0, cash_usd=0,
            whitelist=load_whitelist(db_path),
        )

    cfg = LoopConfig(
        db_path=db_path,
        phase=phase,
        get_portfolio_state=get_portfolio,
    )
    state = LoopRunner(cfg).run_once()
    log.info("Loop finished: outcome=%s run_id=%s", state.outcome, state.run_id)
    sys.exit(0 if state.outcome == "complete" else 1)


if __name__ == "__main__":
    main()

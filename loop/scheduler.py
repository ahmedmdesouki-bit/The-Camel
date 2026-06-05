"""
Windows Task Scheduler entrypoint — runs the paper loop post-market-close.

Usage:
    python loop/scheduler.py

Environment variables:
    NOAH_DB_DIR   directory that holds all seven noah_*.db files
                  (default: repo root)
    NOAH_PHASE    0 | 1 | 2 | 3  (default: 0)
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
    db_dir = os.environ.get(
        "NOAH_DB_DIR",
        str(Path(__file__).resolve().parent.parent),
    )
    phase = int(os.environ.get("NOAH_PHASE", "0"))
    log.info("Scheduler fired. phase=%d db_dir=%s", phase, db_dir)

    from db.paths import NoahDbs, init_all
    dbs = NoahDbs.from_dir(db_dir)
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

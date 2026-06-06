"""
Camel seven-database path registry.

Phase 0 runs seven SQLite files, each owning one data domain.
Caller constructs CamelDbs.from_dir(base_dir) and passes the right
sub-path to each module (e.g. dbs.sharia → sharia/whitelist.py).
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from db.market import init_market_db
from db.sharia import init_sharia_db
from db.portfolio import init_portfolio_db
from db.learning import init_learning_db
from db.macro import init_macro_db
from db.fundamentals import init_fundamentals_db
from db.news import init_news_db


@dataclass
class CamelDbs:
    """Holds paths to all seven Camel databases."""
    market:       str   # prices, dividends, splits
    macro:        str   # rates, inflation, PMIs — stub until Sprint 7
    fundamentals: str   # revenue, margins, EPS — stub until Sprint 7
    news:         str   # structured event objects — stub until Sprint 7
    sharia:       str   # whitelist, sharia_events
    portfolio:    str   # orders, positions, ledger, runs, approvals
    learning:     str   # learning ledger, mistake log

    @classmethod
    def from_dir(cls, base_dir: str) -> "CamelDbs":
        """Build paths under base_dir using the canonical file names."""
        base = Path(base_dir)
        return cls(
            market=str(base / "camel_market.db"),
            macro=str(base / "camel_macro.db"),
            fundamentals=str(base / "camel_fundamentals.db"),
            news=str(base / "camel_news.db"),
            sharia=str(base / "camel_sharia.db"),
            portfolio=str(base / "camel_portfolio.db"),
            learning=str(base / "camel_learning.db"),
        )


def init_all(dbs: CamelDbs) -> None:
    """Initialise all seven databases.  Safe to call on an existing set."""
    init_market_db(dbs.market)
    init_macro_db(dbs.macro)
    init_fundamentals_db(dbs.fundamentals)
    init_news_db(dbs.news)
    init_sharia_db(dbs.sharia)
    init_portfolio_db(dbs.portfolio)
    init_learning_db(dbs.learning)

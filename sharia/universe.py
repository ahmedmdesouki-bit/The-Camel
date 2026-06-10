"""
S16-A4 — the tradeable Sharia universe: founder-approved seeding + the re-screen schedule.

Before this, the whitelist had no production writer and `sharia/cross_check` had no caller, so the
fail-safe `_is_tradeable` guard had no names it could ever clear — a correctly-locked gate in front of
an empty room. This module gives the universe its two missing motions:

  1. `seed_universe` — the FOUNDER adds the starting universe (Sharia-screened ETFs by default:
     SPUS / HLAL — funds whose holdings are screened by their issuer's Sharia board). Every add is
     routed through `Constitution.evaluate(ADD_WHITELIST)` first (founder approval + a logged scan id
     are hard requirements; the agent cannot self-approve a name), then persisted via
     `sharia.whitelist.add_instrument` (which also writes the SHARIA_SCAN audit event).
  2. `rescreen_due` — the quarterly re-screen schedule, as a CALLER: whitelist names whose latest
     `sharia_status` screen is missing or past `next_review_at` are surfaced to the founder daily
     (wired into `loop.jobs.run_daily_ops`). The full automated AAOIFI re-screen via
     `sharia/cross_check` runs per-name once fundamentals data exists for it (S15/EODHD for breadth);
     ETFs re-screen against their issuer's published methodology. Until a name is re-screened, drift
     protection stays fail-safe: cross_check freezes on any non-clear outcome, and a frozen/drifted
     name is close-only (Constitution) and auto-exited (S16-A7 sharia_exit).

CLI (founder-invoked; refuses without --approved-by):
    python -m sharia.universe --approved-by "Chiko" [--symbols SPUS,HLAL] [--db-dir .]
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from db.paths import CamelDbs
from db.sqlite import connection
from guardrail.constitution import Action, ActionType, Constitution, PortfolioState
from sharia.whitelist import add_instrument, load_whitelist

# The starting universe: Sharia-screened, issuer-governed ETFs (whole-share friendly, Sahm-available).
# symbol -> asset_type. Founder extends via the CLI; equities join once fundamentals data lets the
# in-house AAOIFI screen + cross-check actually run on them.
DEFAULT_UNIVERSE: Dict[str, str] = {
    "SPUS": "etf",        # SP Funds S&P 500 Sharia ETF
    "HLAL": "etf",        # Wahed FTSE USA Shariah ETF
}

_REVIEW_DAYS = 90         # quarterly (mirrors sharia/cross_check._REVIEW_DAYS)


def seed_universe(dbs: CamelDbs, approved_by: str, symbols: Optional[Dict[str, str]] = None,
                  source: str = "founder_seed") -> Dict[str, str]:
    """Add the founder-approved universe to the whitelist, one Constitution-gated name at a time.

    FAIL-CLOSED: a blank `approved_by` raises — seeding is a founder act, never an agent default.
    Returns {symbol: 'added' | the Constitution's rejection reason}."""
    if not (approved_by or "").strip():
        raise ValueError("seed_universe requires a founder identity (approved_by) — refusing.")
    symbols = symbols or dict(DEFAULT_UNIVERSE)
    gate = Constitution()
    state = PortfolioState(fund_usd=0.0, cash_usd=0.0)
    today = datetime.now(timezone.utc).date().isoformat()

    results: Dict[str, str] = {}
    for sym, asset_type in symbols.items():
        scan_id = f"seed-{today}-{sym}"
        decision = gate.evaluate(Action(ActionType.ADD_WHITELIST, symbol=sym,
                                        approved_by=approved_by, scan_id=scan_id), state)
        if not decision.allow:
            results[sym] = decision.reason                  # e.g. kill switch active → nothing is added
            continue
        # Sharia is priority #1 and a seed is NOT a screen: only the named DEFAULT_UNIVERSE ETFs
        # (issuer-Sharia-board governed, the basis of the founder's attestation) land 'compliant'.
        # Any OTHER symbol seeds as 'pending_review' — on the list but NOT tradeable (the strategy
        # tradeable-guard and the Constitution's compliant-only buy rule both block it, and A7
        # proposes a de-risk for it if ever held) until a real quorum screen clears it. (QA finding:
        # the old behaviour stamped ANY --symbols name 'compliant' with zero screen behind it.)
        sharia_status = "compliant" if sym in DEFAULT_UNIVERSE else "pending_review"
        add_instrument(dbs.sharia, sym, asset_type, approved_by=approved_by,
                       scan_id=scan_id, source=source, sharia_status=sharia_status)
        results[sym] = f"added ({sharia_status})"
    return results


def _latest_screens(sharia_db: str) -> Dict[str, Tuple[str, str]]:
    """{symbol: (screened_at, next_review_at)} from the newest sharia_status row per symbol.
    Only a MISSING TABLE (no cross-check has ever run) degrades to 'all due'; a real DB failure
    propagates rather than being mislabeled as never-screened (QA finding)."""
    import sqlite3
    out: Dict[str, Tuple[str, str]] = {}
    try:
        with connection(sharia_db) as conn:
            rows = conn.execute(
                "SELECT symbol, screened_at, next_review_at FROM sharia_status "
                "WHERE id IN (SELECT MAX(id) FROM sharia_status GROUP BY symbol)"
            ).fetchall()
        for r in rows:
            out[r["symbol"]] = (r["screened_at"] or "", r["next_review_at"] or "")
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc).lower():
            raise
    return out


def rescreen_due(dbs: CamelDbs, *, now: Optional[datetime] = None) -> List[dict]:
    """Whitelist names whose re-screen is due: never screened by cross_check, or past next_review_at.

    This is the scheduled CALLER the cross-check layer was missing. It reports; it never clears —
    clearing a name takes an actual re-screen (quorum-bound, disagreement→freeze)."""
    now = now or datetime.now(timezone.utc)
    screens = _latest_screens(dbs.sharia)
    due: List[dict] = []
    for sym, inst in sorted(load_whitelist(dbs.sharia).items()):
        screened_at, next_review = screens.get(sym, ("", ""))
        if not screened_at:
            due.append({"symbol": sym, "reason": "never re-screened (whitelist seed only)",
                        "frozen": inst.frozen})
            continue
        try:
            review_at = datetime.fromisoformat(next_review.replace("Z", "+00:00"))
            if review_at.tzinfo is None:
                review_at = review_at.replace(tzinfo=timezone.utc)
        except ValueError:
            due.append({"symbol": sym, "reason": "unparseable next_review_at", "frozen": inst.frozen})
            continue
        if now >= review_at:
            due.append({"symbol": sym, "reason": f"review due since {next_review}",
                        "frozen": inst.frozen})
    return due


def main(argv=None) -> int:                                 # pragma: no cover - CLI entrypoint
    import argparse
    p = argparse.ArgumentParser(description="The Camel — founder-approved Sharia universe seeding")
    p.add_argument("--approved-by", required=True,
                   help="the founder's name — seeding is a founder act (refused when blank)")
    p.add_argument("--symbols", default="",
                   help="comma-separated symbols (default: the Sharia-screened ETF universe)")
    p.add_argument("--asset-type", default="etf")
    p.add_argument("--db-dir", default=os.environ.get("CAMEL_DB_DIR", "."))
    args = p.parse_args(argv)

    from db.paths import init_all
    dbs = CamelDbs.from_dir(args.db_dir)
    init_all(dbs)
    symbols = ({s.strip().upper(): args.asset_type for s in args.symbols.split(",") if s.strip()}
               or None)
    results = seed_universe(dbs, args.approved_by, symbols)
    for sym, status in results.items():
        print(f"  {sym}: {status}")
    due = rescreen_due(dbs)
    if due:
        print(f"re-screen due for {len(due)} name(s): {[d['symbol'] for d in due]}")
    return 0


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())

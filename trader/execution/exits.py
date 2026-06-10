"""
S16-A7 — governed exit / position manager: the generator of closes.

Until now the scheduled decision path was buy-only, so no position ever closed, no round-trip ever
resolved, and the Measure→Learn half (S16-A2) stayed dormant. This module manages the EXISTING book:
it evaluates founder-owned, reduce-only exit rules against open positions and proposes SELL actions.

Trust inversion intact — this module only PROPOSES. Every exit is routed (by `AssembledLoop.run_exits`)
through the same authority chain as a buy: kill switch → Allocator → Constitution (whitelist-required,
close-only for frozen/drifted names, phantom-sell + oversell guards) → phase-gated human approval →
broker. Sells are Edge-exempt by design (de-risking must never be blocked by a missing edge report) and
consume no budget (they free cash).

Rules (founder-owned via `config/limits.yaml`; conservative defaults here):
  sharia_exit  — the instrument is frozen or no longer 'compliant' → close (the Constitution's
                 close-only rule permits exactly this de-risking sell). Highest priority.
  stop_loss    — price ≤ avg_cost·(1 + exit_stop_loss_pct)  → close (the written invalidation, enforced).
  profit_take  — price ≥ avg_cost·(1 + exit_profit_take_pct) → close.
  time_stop    — held longer than exit_time_stop_days → close (a thesis that never resolves is a NO).

Stale-data discipline: a position with NO validated close price is never exited blind — it is skipped
and reported (`skipped_no_price`), honoring "Camel cannot act on stale data".
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from db.sqlite import connection

# founder-owned keys (override in config/limits.yaml); defaults are deliberately conservative
DEFAULT_EXIT_RULES = {
    "exit_profit_take_pct": 0.15,     # +15% → take the profit
    "exit_stop_loss_pct": -0.08,      # −8% → the invalidation point, enforced
    "exit_time_stop_days": 90,        # 90d without resolution → step aside
}

_EPS = 1e-9


@dataclass
class ExitProposal:
    symbol: str
    qty: float
    notional_usd: float               # qty × current close (the sell is sized at the live mark)
    rule: str                         # sharia_exit | stop_loss | profit_take | time_stop
    reason: str


def open_positions(portfolio_db: str) -> List[dict]:
    """Open positions WITH their opened_at (read-only; broker/positions.Position omits the age).

    Only a MISSING TABLE (fresh dir before init_all) degrades to an empty book; any other DB failure
    (lock, corruption) PROPAGATES — a broken book reader must grade the run 'error', never silently
    disable risk management (QA: catch-alls here could switch off every stop-loss without a trace)."""
    try:
        with connection(portfolio_db) as conn:
            rows = conn.execute(
                "SELECT symbol, qty, avg_cost, opened_at FROM positions "
                "WHERE status='open' AND qty > ?", (_EPS,),
            ).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError as exc:
        if "no such table" in str(exc).lower():
            return []
        raise


def last_closes(market_db: str, symbols: List[str]) -> Dict[str, float]:
    """Latest validated POSITIVE close per symbol (read-only). Symbols with no usable price are absent
    (and therefore skipped — never exited blind, never marked-to-market with garbage). Same
    missing-table-only tolerance as `open_positions`."""
    out: Dict[str, float] = {}
    if not symbols:
        return out
    try:
        with connection(market_db) as conn:
            for s in symbols:
                r = conn.execute(
                    "SELECT close FROM prices WHERE symbol=? ORDER BY date DESC LIMIT 1", (s,),
                ).fetchone()
                if r is not None and r[0] is not None and float(r[0]) > 0:
                    out[s] = float(r[0])
    except sqlite3.OperationalError as exc:
        if "no such table" not in str(exc).lower():
            raise
    return out


def _age_days(opened_at: Optional[str], now: datetime) -> Optional[float]:
    if not opened_at:
        return None
    try:
        opened = datetime.fromisoformat(str(opened_at).replace("Z", "+00:00"))
        if opened.tzinfo is None:
            opened = opened.replace(tzinfo=timezone.utc)
        return (now - opened).total_seconds() / 86400.0
    except ValueError:
        return None


def _validate_limits(L: dict) -> None:
    """Founder exit limits must pass a sanity check — a one-character sign typo must fail LOUDLY at
    startup, not liquidate the whole book in one governed tick (QA finding)."""
    if not (float(L["exit_profit_take_pct"]) > 0):
        raise ValueError(f"exit_profit_take_pct must be > 0 (got {L['exit_profit_take_pct']})")
    if not (float(L["exit_stop_loss_pct"]) < 0):
        raise ValueError(f"exit_stop_loss_pct must be < 0 (got {L['exit_stop_loss_pct']})")
    if not (float(L["exit_time_stop_days"]) > 0):
        raise ValueError(f"exit_time_stop_days must be > 0 (got {L['exit_time_stop_days']})")


def evaluate_exits(positions: List[dict], prices: Dict[str, float], whitelist: Dict[str, object], *,
                   limits: Optional[dict] = None, now: Optional[datetime] = None) -> Tuple[List[ExitProposal], List[str]]:
    """Pure rule evaluation → (proposals, skipped_no_price). First matching rule wins, in priority
    order unlisted/sharia_exit > stop_loss > profit_take > time_stop. Full-position closes only (v1).

    Sizing is the EXACT float qty×price — deliberately NOT rounded: the broker reconstructs
    qty = notional/fill_price against an absolute 1e-9 phantom-sell tolerance, and a 6-dp rounding
    perturbs the reconstructed qty above that tolerance for any price below ~$500, randomly refusing
    honest full closes of fractional positions (QA BLOCKER). The broker's full-close clamp is the
    second half of this fix."""
    L = {**DEFAULT_EXIT_RULES, **(limits or {})}
    _validate_limits(L)
    now = now or datetime.now(timezone.utc)
    take = float(L["exit_profit_take_pct"])
    stop = float(L["exit_stop_loss_pct"])
    max_days = float(L["exit_time_stop_days"])

    proposals: List[ExitProposal] = []
    skipped: List[str] = []
    for p in positions:
        sym, qty, avg = p["symbol"], float(p["qty"] or 0.0), float(p["avg_cost"] or 0.0)
        if qty <= _EPS:
            continue
        price = prices.get(sym)
        if price is None or price <= 0:
            skipped.append(sym)                            # stale-data discipline: never exit blind
            continue
        notional = qty * price                             # EXACT — see docstring (QA BLOCKER fix)

        inst = whitelist.get(sym)
        if inst is None:
            # A held name with NO whitelist row is a governed dead-end: the Constitution refuses to
            # sell what it doesn't manage. Propose anyway so the block is VISIBLE every tick (op_log +
            # act detail) instead of an invisible trap — resolving it is a founder act. (QA finding)
            proposals.append(ExitProposal(sym, qty, notional, "unlisted_holding",
                                          f"{sym} is held but has no whitelist row — founder review required"))
            continue
        frozen = bool(getattr(inst, "frozen", False))
        status = (getattr(inst, "sharia_status", "") or "").lower()
        if frozen or status != "compliant":
            proposals.append(ExitProposal(sym, qty, notional, "sharia_exit",
                                          f"{sym} is {'frozen' if frozen else status or 'drifted'} — de-risk (close-only)"))
            continue

        pnl_pct = (price / avg - 1.0) if avg > _EPS else 0.0
        if avg > _EPS and pnl_pct <= stop:
            proposals.append(ExitProposal(sym, qty, notional, "stop_loss",
                                          f"{sym} {pnl_pct:+.1%} ≤ stop {stop:+.1%} — invalidation enforced"))
            continue
        if avg > _EPS and pnl_pct >= take:
            proposals.append(ExitProposal(sym, qty, notional, "profit_take",
                                          f"{sym} {pnl_pct:+.1%} ≥ take {take:+.1%}"))
            continue

        age = _age_days(p.get("opened_at"), now)
        if age is not None and age >= max_days:
            proposals.append(ExitProposal(sym, qty, notional, "time_stop",
                                          f"{sym} held {age:.0f}d ≥ {max_days:.0f}d — thesis unresolved"))
    return proposals, skipped


def build_exit_proposals(dbs, whitelist: Dict[str, object], *, limits: Optional[dict] = None,
                         now: Optional[datetime] = None) -> Tuple[List[ExitProposal], Dict[str, float], List[str]]:
    """Load the open book + live marks and evaluate the rules.

    Returns (proposals, mark_to_market, skipped_no_price). `mark_to_market` is {symbol: qty×close} for
    every open position WITH a price — callers must refresh PortfolioState.positions with it before
    requesting sells, because the positions table carries values at the LAST FILL price; if price rose
    since, the Constitution's oversell guard would otherwise reject an honest full close."""
    pos = open_positions(dbs.portfolio)
    prices = last_closes(dbs.market, [p["symbol"] for p in pos])
    mtm = {p["symbol"]: float(p["qty"]) * prices[p["symbol"]]   # exact — must equal the sell notional
           for p in pos if p["symbol"] in prices}                # bit-for-bit (oversell guard compares them)
    proposals, skipped = evaluate_exits(pos, prices, whitelist, limits=limits, now=now)
    return proposals, mtm, skipped

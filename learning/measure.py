"""
S16 — Measure → Learn: close the operator loop's back half.

Before S16 the §4 loop ran Observe→…→Act and stopped; the `learning/` tiers were correct but called only
by tests. This module is the runtime tail the assembled loop was missing:

    Measure  — record every executed trade as an OPEN decision in the learning_ledger (you cannot learn
               from a decision you never wrote down), then RESOLVE decisions whose position has gone flat
               (realized P&L → win/loss).
    Learn    — feed the resolved wins/losses through the L1 base-rate updater (a NUMBER only), persist the
               per-strategy posterior to `strategy_base_rates`, and — if the anomaly detector flags
               systematic underperformance — file an L3 **propose-only** change request for the founder.

What it deliberately does NOT do (the trust-inversion holds): it never applies a proposal, never edits the
Constitution / limits / weight band, never moves money. It writes numbers and proposals; humans decide.

Resolution (per-round-trip, not lifetime; one outcome per economic close):
  - A decision records the symbol's cumulative realized P&L AT OPEN as a baseline (on the ref). A symbol's
    open decisions resolve when its position is currently `closed` (qty≈0).
  - win/loss is the sign of the ROUND-TRIP P&L = (current cumulative realized − baseline-at-open), NOT the
    sign of lifetime cumulative P&L. So a losing trade after a winning history is correctly a loss.
  - All of a symbol's open decisions are marked resolved by the close, but the close contributes exactly ONE
    win/loss per involved strategy to the base-rate (a single economic round-trip is one outcome, never N).
  - The `actual_outcome IS NULL` filter makes resolution idempotent across ticks (a resolved row is never
    re-counted). Lot-level matching of a decision to a specific partial fill is a future refinement.

KNOWN SCOPE (honest): resolution only fires when a position CLOSES. The current scheduled decision path is
buy-only (the driver proposes side='buy'); nothing in production yet SELLS, so closes — and therefore the
Learn half — do not fire in steady state until the **exit / position-manager (S16-A7)** is wired. The
machinery here is correct and proven by tests that drive a real close; the generator of closes is the
remaining S16 deliverable. Do not describe the loop as auto-closing in production until A7 lands.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from operator_os.learning_ledger import record_decision, record_outcome
from broker.positions import get_position
from learning.base_rate_updater import update_base_rate
from learning.anomaly_detector import detect_underperformance
from learning import improvement_proposer

_REF_PREFIX = "s16"


def _ensure_base_rates(learning_db: str) -> None:
    # Canonical schema lives in db/learning.py; this defensive ensure lets the Learn step run before
    # init_all() on a fresh dir (mirrors the pattern used by ledger/positions/runs writers).
    with connection(learning_db) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS strategy_base_rates ("
            " strategy_id TEXT PRIMARY KEY, base_rate REAL DEFAULT 0.5, n INTEGER DEFAULT 0,"
            " wins INTEGER DEFAULT 0, losses INTEGER DEFAULT 0, updated_at TEXT)"
        )


def _ensure_proposals(learning_db: str) -> None:
    # Defensive ensure so an L3 underperformance proposal is never silently dropped on a dir where
    # init_all() has not run (improvement_proposer.propose itself does no CREATE). Mirrors db/learning.py.
    with connection(learning_db) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS learning_proposals ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now')),"
            " proposal_type TEXT, strategy_id TEXT, detail TEXT, rationale TEXT,"
            " status TEXT DEFAULT 'pending', decided_by TEXT, decided_at TEXT)"
        )


def _encode_ref(symbol: str, strategies: List[str], base: float) -> str:
    # `base` = the symbol's cumulative realized P&L at the moment this decision opened, so the round-trip
    # P&L can be computed as a DELTA at close (never the mislabel-prone lifetime cumulative).
    return f"{_REF_PREFIX}|sym:{symbol}|strat:{','.join(strategies)}|base:{round(base, 6)}"


def _decode_ref(ref: str) -> Dict[str, object]:
    out: Dict[str, object] = {"symbol": "", "strategies": [], "base": 0.0}
    for part in (ref or "").split("|"):
        if part.startswith("sym:"):
            out["symbol"] = part[4:]
        elif part.startswith("strat:"):
            out["strategies"] = [s for s in part[6:].split(",") if s]
        elif part.startswith("base:"):
            try:
                out["base"] = float(part[5:])
            except ValueError:                              # pragma: no cover - defensive
                out["base"] = 0.0
    return out


def record_trade_decision(dbs: CamelDbs, symbol: str, strategies: List[str], *,
                          base_rate_expectation: float = 0.5, thesis_summary: str = "") -> int:
    """Measure substrate: write one executed trade as an OPEN decision (actual_outcome NULL), snapshotting
    the symbol's cumulative realized P&L now so the round-trip's own P&L is recoverable at close."""
    strategies = sorted(set(strategies or []))
    pos = get_position(dbs.portfolio, symbol)
    base = pos.realized_pnl if pos else 0.0                  # cumulative realized at open = round-trip baseline
    summary = thesis_summary or f"{symbol} via {'/'.join(strategies) or 'unattributed'}"
    return record_decision(
        dbs.learning, "TRADE", thesis_summary=summary,
        expected_outcome=f"base_rate≈{round(base_rate_expectation, 4)}",
        ref=_encode_ref(symbol, strategies, base),
    )


def _open_trade_decisions(learning_db: str) -> List[dict]:
    with connection(learning_db) as conn:
        rows = conn.execute(
            "SELECT id, ref FROM learning_ledger "
            "WHERE decision_type='TRADE' AND (actual_outcome IS NULL OR actual_outcome='') "
            "AND ref LIKE ? ORDER BY id ASC",
            (f"{_REF_PREFIX}|%",),
        ).fetchall()
    return [dict(r) for r in rows]


def _read_base_rate(learning_db: str, strategy_id: str, seed_rate: float) -> Dict[str, float]:
    with connection(learning_db) as conn:
        r = conn.execute(
            "SELECT base_rate, n, wins, losses FROM strategy_base_rates WHERE strategy_id=?",
            (strategy_id,),
        ).fetchone()
    if r is None:
        return {"base_rate": round(seed_rate, 4), "n": 0, "wins": 0, "losses": 0}
    return {"base_rate": r["base_rate"], "n": r["n"], "wins": r["wins"], "losses": r["losses"]}


def _write_base_rate(learning_db: str, strategy_id: str, base_rate: float,
                     n: int, wins: int, losses: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connection(learning_db) as conn:
        conn.execute(
            "INSERT INTO strategy_base_rates (strategy_id, base_rate, n, wins, losses, updated_at) "
            "VALUES (?,?,?,?,?,?) ON CONFLICT(strategy_id) DO UPDATE SET "
            "base_rate=excluded.base_rate, n=excluded.n, wins=excluded.wins, "
            "losses=excluded.losses, updated_at=excluded.updated_at",
            (strategy_id, round(base_rate, 4), n, wins, losses, now),
        )


def _seed_rate_from_registry(registry, strategy_id: str) -> float:
    """A strategy's declared prior hit-rate, if the registry exposes it; else the neutral 0.5."""
    if registry is None:
        return 0.5
    for getter in ("lookup", "get"):
        fn = getattr(registry, getter, None)
        if callable(fn):
            try:
                strat = fn(strategy_id)
                meta = getattr(strat, "meta", None)
                return float(getattr(meta, "base_rate", 0.5))
            except Exception:                                   # pragma: no cover - registry shape varies
                pass
    return 0.5


def resolve_and_learn(dbs: CamelDbs, *, registry=None) -> dict:
    """Resolve round-tripped trades → update per-strategy base-rates (L1) → propose on anomaly (L3).

    One economic close = ONE outcome per involved strategy (never N, even if several open decisions share
    the symbol). win/loss is the ROUND-TRIP P&L (realized-since-open delta), not lifetime cumulative.
    Returns a summary. Propose-only: it never applies a change, edits a rule, or moves money.
    """
    _ensure_base_rates(dbs.learning)
    _ensure_proposals(dbs.learning)

    # group every open TRADE decision by symbol so one close resolves the symbol's round-trip as a unit
    by_symbol: Dict[str, list] = {}
    for dec in _open_trade_decisions(dbs.learning):
        info = _decode_ref(dec["ref"])
        symbol = str(info["symbol"])
        if not symbol:
            continue
        by_symbol.setdefault(symbol, []).append((dec, info))

    resolved = 0           # decision rows closed (may exceed round_trips when decisions share a symbol)
    round_trips = 0        # economic closes (the unit of a learning outcome)
    tally: Dict[str, Dict[str, int]] = {}

    for symbol, decs in by_symbol.items():
        pos = get_position(dbs.portfolio, symbol)
        # resolve only a completed round-trip: the symbol's position is currently flat/closed
        if pos is None or pos.status != "closed" or pos.qty > 1e-9:
            continue
        # round-trip P&L = realized since the round-trip OPENED (the earliest baseline among these
        # decisions; the position was continuously open from then to this close, so no other realized
        # event lies between). This is the per-trade result — NOT the sign of lifetime cumulative P&L.
        base = min(float(info["base"]) for _d, info in decs)
        round_trip_pnl = round(pos.realized_pnl - base, 4)
        round_trips += 1
        # A zero-delta close carries NO win/loss signal — a true break-even, OR a decision recorded against
        # an already-flat symbol (library misuse the production caller can't reach). Mark it resolved but
        # tally NO outcome, so it can never become a phantom loss that pollutes the base-rate.
        scored = round_trip_pnl != 0
        won = round_trip_pnl > 0

        strategies_in_rt = set()
        for dec, info in decs:
            record_outcome(
                dbs.learning, dec["id"],
                actual_outcome=f"closed round_trip_pnl={round_trip_pnl}",
                mistake_type=("OK" if (won or not scored) else "SIGNAL_ERROR"),
                lesson_learned=("edge held" if won else
                                "break-even — no signal" if not scored else
                                "edge did not hold — review signal"),
            )
            resolved += 1
            for sid in (info["strategies"] or ["unattributed"]):
                strategies_in_rt.add(sid)
        # exactly ONE win/loss per strategy for this single economic round-trip (no over-count); a
        # zero-delta round-trip scores nothing.
        if scored:
            for sid in strategies_in_rt:
                t = tally.setdefault(sid, {"wins": 0, "losses": 0})
                t["wins" if won else "losses"] += 1

    strategies_updated: List[dict] = []
    proposals: List[int] = []
    for sid, t in tally.items():
        seed = _seed_rate_from_registry(registry, sid)      # the strategy's DECLARED expectation (stable)
        cur = _read_base_rate(dbs.learning, sid, seed)
        wins, losses = t["wins"], t["losses"]
        posterior = update_base_rate(cur["base_rate"], cur["n"], wins, losses)   # L1 — a NUMBER only
        new_n = cur["n"] + wins + losses
        new_wins, new_losses = cur["wins"] + wins, cur["losses"] + losses
        _write_base_rate(dbs.learning, sid, posterior, new_n, new_wins, new_losses)

        # Anomaly: the strategy's CUMULATIVE realized hit-rate vs its DECLARED expectation, gated on the
        # cumulative sample. Both numerator and denominator are cumulative — no batch/cumulative mismatch,
        # and the reference is stable (so a drifting posterior can't mask sustained underperformance).
        realized_cumulative = round(new_wins / new_n, 4) if new_n else 0.0
        flag = detect_underperformance(realized_cumulative, seed, new_n)
        strategies_updated.append({"strategy_id": sid, "base_rate": posterior, "n": new_n,
                                   "realized_hit_rate": realized_cumulative, "flagged": flag.flagged})
        if flag.flagged:
            # L3 — PROPOSE ONLY. The founder (L4) approves/rejects out-of-band; nothing auto-applies.
            pid = improvement_proposer.propose(
                dbs, "cooldown", strategy_id=sid,
                detail={"realized_hit_rate": realized_cumulative, "declared_base_rate": seed, "n": new_n},
                rationale=flag.note,
            )
            proposals.append(pid)

    return {"resolved": resolved, "round_trips": round_trips,
            "strategies_updated": strategies_updated, "proposals": proposals}

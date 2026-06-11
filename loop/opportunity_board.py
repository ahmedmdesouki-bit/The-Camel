"""
S17.6 — The Opportunity Board: the CONDUCTOR's answer to "where do I put my money?"

It synthesizes the desks' read of the world — ORACLE's regime, MUFTI's Sharia status, QUANT's Edge-Proof
verdict — into a RANKED, REASONED proposal per candidate name, each carrying its full reason chain. This is
the founder-facing "insight," and it is honest by construction:

  * Sharia is priority #1: a non-compliant / frozen name is `avoid`, never proposed for a buy — full stop.
  * A name with a CONFIRMED edge (QUANT) → `buy` proposal (highest score).
  * A compliant name with NO edge → `dca` (DCA into the compliant core is the humble default, a SUCCESS
    state, not a failure — the system is telling you it has no edge here).
  * A risk-off regime lowers scores (defensive tilt); the human still decides.

Crucially this board only PROPOSES. Nothing here moves money: acting on a row still runs through the
governed tick (Edge Proof → Constitution → Budget → Approval → Broker). Building the board writes ONLY the
`opportunity_proposals` audit table — never orders, ledger, or positions.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection

_RISK_OFF = ("RECESSION_RISK", "GEOPOLITICAL_RISK_OFF", "INFLATION_SHOCK")
_COMPLIANT = ("pass", "compliant")


@dataclass
class Proposal:
    symbol: str
    action: str                      # buy | dca | wait | avoid
    score: float
    regime: str
    sharia_status: str
    edge_allowed: bool
    hit_rate: float
    sample_size: int
    confidence: float
    recommended_action: str
    invalidation: str
    reason_chain: List[str] = field(default_factory=list)


def _ensure_table(learning_db: str) -> None:
    with connection(learning_db) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS opportunity_proposals ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT DEFAULT (datetime('now')), symbol TEXT,"
            " action TEXT, score REAL, regime TEXT, sharia_status TEXT, edge_allowed INTEGER,"
            " hit_rate REAL, sample_size INTEGER, confidence REAL, recommended_action TEXT,"
            " invalidation TEXT, reason_chain TEXT, status TEXT DEFAULT 'proposed', founder_rank REAL,"
            " decided_by TEXT, decided_at TEXT)")


def _current_regime(dbs: CamelDbs) -> str:
    try:
        with connection(dbs.macro) as conn:
            r = conn.execute("SELECT regime FROM regime_history ORDER BY id DESC LIMIT 1").fetchone()
        return r["regime"] if r else "UNKNOWN"
    except Exception:                                         # no regime table yet
        return "UNKNOWN"


def _symbol_sharia(dbs: CamelDbs, symbol: str) -> str:
    """The name's Sharia state for the board. Fail-safe ordering: a LIVE freeze always wins (a frozen name
    is non-compliant even if an older screen row still says 'pass' — review LOW), then the latest
    multi-state screen, then the whitelist status, then 'unknown'. Anything not a clear pass blocks a buy."""
    from sharia.whitelist import get_instrument
    inst = get_instrument(dbs.sharia, symbol)
    if inst and inst.get("frozen"):
        return "frozen"                                      # a live freeze overrides any stale screen
    try:
        with connection(dbs.sharia) as conn:
            r = conn.execute("SELECT final_status FROM sharia_status WHERE symbol=? ORDER BY id DESC LIMIT 1",
                             (symbol,)).fetchone()
        if r and r[0]:
            return r[0]
    except Exception:
        pass
    if inst:
        return inst.get("sharia_status") or "unknown"
    return "unknown"


def _candidates(dbs: CamelDbs, symbols: Optional[List[str]]) -> List[str]:
    if symbols:
        return [s.strip().upper() for s in symbols if s.strip()]
    from sharia.whitelist import load_whitelist
    return sorted(load_whitelist(dbs.sharia).keys())


def build_board(dbs: CamelDbs, *, symbols: Optional[List[str]] = None,
                edge_fn: Optional[Callable] = None, persist: bool = True) -> List[Proposal]:
    """Assemble the ranked Opportunity Board. `edge_fn(dbs, symbol)` is injectable (defaults to the real
    17-check Edge Proof) so the assembly is deterministically testable. Returns proposals, highest score
    first. PROPOSES only — writes nothing but the proposals audit table."""
    if edge_fn is None:
        from trader.engine.edge_proof import evaluate_signal_full
        def edge_fn(_dbs, _sym):
            return evaluate_signal_full(_dbs, _sym, signal="board", signal_definition="conductor:board",
                                        mode="enforcing")

    regime = _current_regime(dbs)
    risk_off = regime in _RISK_OFF
    out: List[Proposal] = []

    for sym in _candidates(dbs, symbols):
        sharia = _symbol_sharia(dbs, sym)
        compliant = sharia.lower() in _COMPLIANT
        try:
            rep = edge_fn(dbs, sym)
        except Exception:
            rep = None
        allowed = bool(getattr(rep, "trade_allowed", False)) if rep is not None else False
        hit = float(getattr(rep, "hit_rate", 0.0) or 0.0) if rep is not None else 0.0
        n = int(getattr(rep, "sample_size", 0) or 0) if rep is not None else 0
        edge_reason = (getattr(rep, "reason", "") or "") if rep is not None else "no edge report"

        reasons = [f"Sharia: {sharia}",
                   f"Regime: {regime}{' (risk-off)' if risk_off else ''}",
                   f"Edge: {'CONFIRMED' if allowed else 'none'} (hit_rate={hit:.0%}, n={n}) — {edge_reason}"]

        if not compliant:                                    # priority #1 — a hard wall, never a buy
            action, score, conf, rec = "avoid", 0.0, 0.9, "not Sharia-clear → exclude (reduce-only if held)"
        elif allowed:
            action, score, conf = "buy", round(2.0 + hit - (0.5 if risk_off else 0.0), 4), hit
            rec = "edge proven → propose buy (founder approves; tick executes)"
        else:
            action, score, conf = "dca", round(1.0 - (0.3 if risk_off else 0.0), 4), 0.3
            rec = "no edge → DCA into the compliant core (a success state, not a failure)"

        out.append(Proposal(
            symbol=sym, action=action, score=score, regime=regime, sharia_status=sharia,
            edge_allowed=allowed, hit_rate=hit, sample_size=n, confidence=conf,
            recommended_action=rec, invalidation=(edge_reason or "edge decays / Sharia drift"),
            reason_chain=reasons))

    out.sort(key=lambda p: p.score, reverse=True)
    if persist:
        _persist(dbs, out)
    return out


def _persist(dbs: CamelDbs, proposals: List[Proposal]) -> None:
    """Supersede the prior live board (mark 'proposed' → 'expired') and write the new one. Approved/vetoed
    rows are left untouched as an audit trail."""
    _ensure_table(dbs.learning)
    with connection(dbs.learning) as conn:
        conn.execute("UPDATE opportunity_proposals SET status='expired' WHERE status='proposed'")
        for p in proposals:
            conn.execute(
                "INSERT INTO opportunity_proposals (symbol, action, score, regime, sharia_status, "
                "edge_allowed, hit_rate, sample_size, confidence, recommended_action, invalidation, "
                "reason_chain, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?, 'proposed')",
                (p.symbol, p.action, p.score, p.regime, p.sharia_status, 1 if p.edge_allowed else 0,
                 p.hit_rate, p.sample_size, p.confidence, p.recommended_action, p.invalidation,
                 json.dumps(p.reason_chain)))


def current_board(dbs: CamelDbs) -> List[dict]:
    """The live board (status='proposed'), highest priority first — what the Kitchen renders. A founder
    reorder (`founder_rank`) overrides the computed score for ordering."""
    _ensure_table(dbs.learning)
    with connection(dbs.learning) as conn:
        rows = conn.execute(
            "SELECT * FROM opportunity_proposals WHERE status='proposed' "
            "ORDER BY COALESCE(founder_rank, score) DESC, id ASC"
        ).fetchall()
    return [dict(r) for r in rows]


# ---- founder controls (the Kitchen; invoked by the founder-only command channel — S17.7) ----

def decide_proposal(dbs: CamelDbs, proposal_id: int, approve: bool, by: str) -> bool:
    """Founder approves/vetoes a board row. A PROPOSAL decision only — it records intent; acting on an
    approved proposal still runs through the governed tick. Returns True if a 'proposed' row was updated."""
    import datetime as _dt
    _ensure_table(dbs.learning)
    with connection(dbs.learning) as conn:
        cur = conn.execute(
            "UPDATE opportunity_proposals SET status=?, decided_by=?, decided_at=? "
            "WHERE id=? AND status='proposed'",
            ("approved" if approve else "vetoed", by,
             _dt.datetime.now(_dt.timezone.utc).isoformat(), int(proposal_id)))
        return cur.rowcount > 0


def prioritize_proposal(dbs: CamelDbs, proposal_id: int, rank: float) -> bool:
    """Founder reorders the board (higher rank = higher in the Kitchen). Overrides the computed score for
    ordering only — it never changes the governed verdict."""
    _ensure_table(dbs.learning)
    with connection(dbs.learning) as conn:
        cur = conn.execute(
            "UPDATE opportunity_proposals SET founder_rank=? WHERE id=? AND status='proposed'",
            (float(rank), int(proposal_id)))
        return cur.rowcount > 0


def main(argv=None) -> int:                                  # pragma: no cover - CLI entrypoint
    import argparse
    import os
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")             # Windows cp1252 console can't print →/—
    except Exception:
        pass
    p = argparse.ArgumentParser(description="The Camel — build the Opportunity Board")
    p.add_argument("--db-dir", default=os.environ.get("CAMEL_DB_DIR", "."))
    p.add_argument("--symbols", default=os.environ.get("CAMEL_SYMBOLS", ""))
    args = p.parse_args(argv)
    from db.paths import init_all
    dbs = CamelDbs.from_dir(args.db_dir)
    init_all(dbs)
    syms = [s.strip() for s in args.symbols.split(",") if s.strip()] or None
    board = build_board(dbs, symbols=syms)
    print(f"Opportunity Board ({len(board)} candidates):")
    for p in board:
        print(f"  {p.symbol:<6} {p.action.upper():<6} score={p.score:<5} — {p.recommended_action}")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())

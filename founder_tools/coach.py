"""
camel-coach (founder-tools, Workstream C) — read-only conversational Q&A over the Camel's governed state.

It REPORTS; it never ACTS and never ADVISES. It reads the same snapshot the dashboard renders and answers
plain questions ("status", "positions", "board", "why SPUS", "regime", "safety", "desks", "edge"). It has
NO path to the broker, the ledger, the Constitution, or any config — it cannot move money or change a rule,
and it explicitly DECLINES to give a buy/sell recommendation (that is the governed loop's job — Edge Proof
-> Constitution -> founder approval — not a chat answer). Deterministic over the snapshot, fully testable
offline.

CLI:  python -m founder_tools.coach "status"
"""
from __future__ import annotations

from db.paths import CamelDbs
from dashboard.snapshot import build_snapshot

_FOOTER = "\n(read-only view of the governed state — not financial or Sharia advice)"

# Asking for a recommendation is declined by design — the coach reports, it does not advise.
_ADVICE_TELLS = ("should i", "do you recommend", "is it a good", "will it go", "buy or sell",
                 "what should i buy", "what should i sell", "is now a good time")


def _status(s: dict) -> str:
    k, g, h = s["kpis"], s["governance"], s["health"]
    return (f"Status: {h['status']} · {g['phase_label']} · kill switch {g['kill_switch']}\n"
            f"Total value ${k['total_value']:.2f} ({k['open_positions']} open position(s)) · "
            f"cash ${k['cash']:.2f} (drag {k['cash_drag_pct']:.1f}%)\n"
            f"Unrealised ${k['unrealized_pnl']:.2f} · realised ${k['realized_pnl']:.2f}\n"
            f"Live-money gate: {g['gate_passed']}/{g['gate_total']} clear · live at risk "
            f"${g['live_at_risk']:.0f}")


def _positions(s: dict) -> str:
    ps = [p for p in s["positions"] if (p.get("status") or "open") == "open"]
    if not ps:
        return "No open positions."
    lines = [f"  {p['symbol']:<6} qty {p['qty']} @ ${p['avg_cost']} · mv ${p['market_value']} · "
             f"uPnL ${p['unrealized_pnl']}" for p in ps]
    return "Open positions:\n" + "\n".join(lines)


def _board(s: dict) -> str:
    b = s["board"]
    if not b:
        return "The Opportunity Board is empty."
    lines = [f"  {r['symbol']:<6} {str(r['action']).upper():<5} score {r['score']} — "
             f"{r['recommended_action']}" for r in b]
    return "Opportunity Board:\n" + "\n".join(lines)


def _regime(s: dict) -> str:
    r = s["regime"]
    if not r:
        return "No regime classified yet (macro data not ingested)."
    sigs = ", ".join(r["signals"][:4]) if r.get("signals") else "no signals"
    return f"Regime: {r['regime']} (confidence {r['confidence']}) — {sigs}"


def _safety(s: dict) -> str:
    g = s["governance"]
    lines = [f"  [{'x' if it['ok'] else ' '}] {it['label']}" for it in g["gate_items"]]
    return f"Live-money safety gate ({g['gate_passed']}/{g['gate_total']}):\n" + "\n".join(lines)


def _desks(s: dict) -> str:
    d = s["desks"]
    if not d:
        return "No desk runs recorded yet."
    lines = [f"  {x['desk_id']:<10} {x['status']:<7} {x['summary']}"
             + (" (paused)" if x.get("paused") else "") for x in d]
    return "Workforce desks:\n" + "\n".join(lines)


def _edge(s: dict) -> str:
    e = s["edge_decisions"]
    if not e:
        return "No Edge-Proof decisions recorded yet."
    lines = [f"  {x['symbol']}: {'ALLOWED' if x['trade_allowed'] else 'blocked'} — {x['reason']}"
             for x in e[:6]]
    return "Recent Edge-Proof verdicts:\n" + "\n".join(lines)


def _why(s: dict, symbol: str) -> str:
    sym = (symbol or "").upper().strip()
    for r in s["board"]:
        if (r.get("symbol") or "").upper() == sym:
            chain = ("\n   - " + "\n   - ".join(r["reason_chain"])) if r.get("reason_chain") else \
                    " (no reason chain)"
            return f"{sym}: {str(r['action']).upper()} (score {r['score']})\nReason chain:{chain}"
    return f"{sym} is not on the current Opportunity Board."


def _help() -> str:
    return ("Ask me about: status · positions · board · why <SYMBOL> · regime · safety · desks · edge. "
            "I report the governed state; I don't advise or trade.")


def coach(dbs: CamelDbs, question: str, *, mode: str = "paper") -> str:
    """Answer one read-only question about the governed state. Never advises, never acts."""
    q = (question or "").strip()
    ql = q.lower()
    if any(t in ql for t in _ADVICE_TELLS):
        return ("I won't give a buy/sell recommendation — that's the governed loop's job (Edge Proof -> "
                "Constitution -> your approval), not a chat answer. I can show you the board, the edge "
                "verdicts, and a name's reason chain so YOU decide." + _FOOTER)

    s = build_snapshot(dbs, mode=mode)
    if ql.startswith("why ") and len(q.split(None, 1)) == 2:
        return _why(s, q.split(None, 1)[1]) + _FOOTER

    routes = [
        (("status", "posture", "overall", "how are we"), _status),
        (("position", "holding", "portfolio"), _positions),
        (("board", "opportunit"), _board),
        (("regime", "macro"), _regime),
        (("safe", "gate", "risk"), _safety),
        (("desk", "workforce"), _desks),
        (("edge",), _edge),
    ]
    for keys, fn in routes:
        if any(k in ql for k in keys):
            return fn(s) + _FOOTER
    return _help() + _FOOTER


def main(argv=None) -> int:                                  # pragma: no cover - CLI entrypoint
    import argparse
    import os
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="camel-coach — read-only Q&A over the governed state")
    p.add_argument("question", nargs="*", default=["status"])
    p.add_argument("--db-dir", default=os.environ.get("CAMEL_DB_DIR", "."))
    args = p.parse_args(argv)
    from db.paths import init_all
    dbs = CamelDbs.from_dir(args.db_dir)
    init_all(dbs)
    print(coach(dbs, " ".join(args.question) if isinstance(args.question, list) else args.question))
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())

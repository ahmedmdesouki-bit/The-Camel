"""
S17.1 — The Workforce: the one governed loop, decomposed into named single-job DESKS.

A desk has one job and emits a structured `DeskResult` (and, if it is an analyst, `EvidenceObject`s against
the S12.5 contract). This generalizes the dormant `research/` Research-Desk framework into the runtime
workforce — WITHOUT changing the trust-inversion:

  * EVIDENCE desks (HERALD/ORACLE/MUFTI/QUANT) extend `EvidenceDesk`, which inherits `research.desk.AnalystDesk`
    — a class with NO act/execute/trade method anywhere. They read the governed DBs and write EvidenceObjects.
    They cannot move money. (A test pins this.)
  * OPERATOR desks (SCOUT/STEWARD/CONDUCTOR) extend `OperatorDesk`. They may touch the governed runtime, but
    only through the EXISTING gated paths: SCOUT writes data tables only; STEWARD reads + runs reduce-only
    governed exits; CONDUCTOR is the SOLE desk that can cause a buy, and only via Edge Proof → Constitution →
    Budget → Approval → Broker. No desk gets a path around a gate.

`Workforce.run_desk` runs each desk in ISOLATION (one desk's failure never aborts the rest), times it, and
appends a `desk_runs` audit row — the spine the Supervisor (S17.2) and the Kitchen (S17.7) build on.

CLI:
    python -m research.workforce list
    python -m research.workforce run <desk_id> [--symbols SPUS,HLAL]
    python -m research.workforce cycle      [--symbols SPUS,HLAL]
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from research.desk import AnalystDesk, write_evidence
from research.evidence import EvidenceObject

# attributes a desk must NOT expose to keep the trust-inversion — an evidence desk that grew one of these
# would be a path to act outside the gates. The no-act test asserts none are present on evidence desks.
FORBIDDEN_ACT_ATTRS = ("act", "execute", "execute_order", "trade", "submit", "submit_order", "buy", "sell",
                       "order", "place", "place_order", "fill", "broker", "run_exits", "run_tick", "request")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DeskResult:
    desk_id: str
    status: str = "ok"                       # ok | empty | error
    summary: str = ""
    evidence: List[EvidenceObject] = field(default_factory=list)
    outputs: Dict = field(default_factory=dict)
    metrics: Dict = field(default_factory=dict)
    started_at: str = ""
    ended_at: str = ""
    error: str = ""


class Desk:
    """A single-job desk. Subclasses set `desk_id` and `kind` and implement `run`."""
    desk_id: str = "base"
    kind: str = "operator"                   # "evidence" | "operator"

    def run(self, dbs: CamelDbs, ctx: Optional[Dict] = None) -> DeskResult:   # pragma: no cover - abstract
        raise NotImplementedError


class EvidenceDesk(Desk, AnalystDesk):
    """An analyst desk: reads governed DBs, emits EvidenceObjects, persists them — and CANNOT act.
    Inherits AnalystDesk (no act method); subclasses implement `analyze`. `run` is final-ish here so no
    subclass accidentally introduces an execute path."""
    kind = "evidence"

    def run(self, dbs: CamelDbs, ctx: Optional[Dict] = None) -> DeskResult:
        started = _utcnow()
        notes = [e for e in self.analyze(dbs, ctx) if e.valid()]
        for ev in notes:
            write_evidence(dbs, ev)          # evidence flows ONLY into research_evidence
        status = "ok" if notes else "empty"
        return DeskResult(self.desk_id, status, summary=f"{len(notes)} evidence note(s)",
                          evidence=notes, metrics={"evidence_n": len(notes)},
                          started_at=started, ended_at=_utcnow())


class OperatorDesk(Desk):
    """A desk that touches the governed runtime — but only via existing gated paths. Subclasses implement
    `run`. (There is no generic act helper here; each operator desk calls the specific governed function.)"""
    kind = "operator"


# ---- audit ----

def _ensure_desk_runs(learning_db: str) -> None:
    # Single source of truth is db/learning.py.
    from db.learning import init_learning_db
    init_learning_db(learning_db)


def record_desk_run(dbs: CamelDbs, r: DeskResult) -> int:
    _ensure_desk_runs(dbs.learning)
    with connection(dbs.learning) as conn:
        cur = conn.execute(
            "INSERT INTO desk_runs (desk_id, status, summary, metrics, evidence_n, started_at, ended_at, error)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (r.desk_id, r.status, r.summary, json.dumps(r.metrics), len(r.evidence),
             r.started_at, r.ended_at, r.error))
        return cur.lastrowid


def latest_desk_status(dbs: CamelDbs) -> Dict[str, dict]:
    """{desk_id: {status, summary, ts, evidence_n}} from the newest desk_runs row per desk — the Kitchen view."""
    _ensure_desk_runs(dbs.learning)
    with connection(dbs.learning) as conn:
        rows = conn.execute(
            "SELECT desk_id, status, summary, ts, evidence_n, error FROM desk_runs "
            "WHERE id IN (SELECT MAX(id) FROM desk_runs GROUP BY desk_id)").fetchall()
    return {r["desk_id"]: {"status": r["status"], "summary": r["summary"], "ts": r["ts"],
                           "evidence_n": r["evidence_n"], "error": r["error"]} for r in rows}


# ---- the registry / runner ----

class Workforce:
    def __init__(self):
        self._desks: Dict[str, Desk] = {}

    def register(self, desk: Desk) -> "Workforce":
        self._desks[desk.desk_id] = desk
        return self

    def get(self, desk_id: str) -> Optional[Desk]:
        return self._desks.get(desk_id)

    def desk_ids(self) -> List[str]:
        return list(self._desks)

    def run_desk(self, dbs: CamelDbs, desk_id: str, ctx: Optional[Dict] = None) -> DeskResult:
        """Run ONE desk in isolation — any failure is captured as a status='error' result (never raised),
        then audited. This is the isolation the Supervisor (S17.2) extends with retry/quarantine."""
        desk = self._desks.get(desk_id)
        if desk is None:
            r = DeskResult(desk_id, "error", error=f"unknown desk {desk_id!r}",
                           started_at=_utcnow(), ended_at=_utcnow())
            return r
        # S17.7 — a founder-paused desk runs nothing (the Kitchen's grip on the workforce)
        from governance.desk_control import is_paused
        if is_paused(dbs, desk_id):
            r = DeskResult(desk_id, "paused", summary="paused by founder",
                           started_at=_utcnow(), ended_at=_utcnow())
            record_desk_run(dbs, r)
            return r
        started = _utcnow()
        try:
            r = desk.run(dbs, ctx)
            if not r.started_at:
                r.started_at = started
            if not r.ended_at:
                r.ended_at = _utcnow()
        except Exception as exc:                          # one desk failing must not stop the workforce
            r = DeskResult(desk_id, "error", error=str(exc), started_at=started, ended_at=_utcnow())
        record_desk_run(dbs, r)
        return r

    def run_all(self, dbs: CamelDbs, ctx: Optional[Dict] = None,
                order: Optional[List[str]] = None) -> List[DeskResult]:
        return [self.run_desk(dbs, did, ctx) for did in (order or self.desk_ids())]


def default_workforce() -> Workforce:
    """The 7-desk roster, in dependency order (SCOUT→HERALD/ORACLE/MUFTI→QUANT→STEWARD→CONDUCTOR)."""
    from research.roster import (ScoutDesk, HeraldDesk, OracleDesk, MuftiDesk, QuantDesk,
                                 StewardDesk, ConductorDesk)
    wf = Workforce()
    for d in (ScoutDesk(), HeraldDesk(), OracleDesk(), MuftiDesk(), QuantDesk(),
              StewardDesk(), ConductorDesk()):
        wf.register(d)
    return wf


def main(argv=None) -> int:                               # pragma: no cover - CLI entrypoint
    import argparse
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")          # Windows cp1252 console can't print →/—
    except Exception:
        pass
    p = argparse.ArgumentParser(description="The Camel — the desk workforce")
    p.add_argument("cmd", choices=["list", "run", "cycle"])
    p.add_argument("desk", nargs="?", default="")
    p.add_argument("--db-dir", default=os.environ.get("CAMEL_DB_DIR", "."))
    p.add_argument("--symbols", default=os.environ.get("CAMEL_SYMBOLS", ""))
    args = p.parse_args(argv)

    from db.paths import init_all
    dbs = CamelDbs.from_dir(args.db_dir)
    init_all(dbs)
    wf = default_workforce()
    ctx = {"symbols": [s.strip().upper() for s in args.symbols.split(",") if s.strip()]}

    if args.cmd == "list":
        for did in wf.desk_ids():
            print(f"  {did:<10} ({wf.get(did).kind})")
        return 0
    results = ([wf.run_desk(dbs, args.desk, ctx)] if args.cmd == "run"
               else wf.run_all(dbs, ctx))
    for r in results:
        print(f"  {r.desk_id:<10} {r.status:<6} {r.summary}" + (f"  ERR: {r.error}" if r.error else ""))
    return 0


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main())

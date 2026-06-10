"""
S17.1 — the 7-desk roster. Each desk has one job and wraps an engine The Camel already built; none of
them is new trading logic. Evidence desks read governed DBs and emit EvidenceObjects (they cannot act);
operator desks touch the runtime only through existing gated paths.

    SCOUT     find data (ingest)                         operator — writes data DBs only
    HERALD    gather notable news/events                 evidence
    ORACLE    macro regime + peg                         evidence (delegates to research.desks.MacroDesk)
    MUFTI     Sharia compliance + drift                  evidence (delegates to research.desks.ShariaDesk)
    QUANT     the edge (17-check proof) per name         evidence
    STEWARD   portfolio — cash, positions, fund          operator — read-only summary (exits run in the tick)
    CONDUCTOR assemble evidence (S17.6 builds the board) operator — the SOLE buy path, still fully gated
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from research.evidence import EvidenceObject
from research.workforce import EvidenceDesk, OperatorDesk, DeskResult


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _whitelist_symbols(dbs: CamelDbs) -> List[str]:
    from sharia.whitelist import load_whitelist
    return sorted(load_whitelist(dbs.sharia).keys())


# ---- SCOUT (operator) — the only desk that pulls external data; writes data DBs only ----

class ScoutDesk(OperatorDesk):
    desk_id = "scout"

    def run(self, dbs: CamelDbs, ctx: Optional[Dict] = None) -> DeskResult:
        ctx = ctx or {}
        started = _utcnow()
        from data.ingest import default_jobs, run_ingestion
        jobs = default_jobs(ctx.get("symbols") or [], ctx.get("series") or [], ctx.get("ciks") or [])
        res = run_ingestion(dbs, jobs, transport=ctx.get("transport"))
        stored = sum(v.get("stored", 0) for v in res.values() if isinstance(v, dict))
        return DeskResult(self.desk_id, "ok" if stored else "empty",
                          summary=f"ingested {stored} row(s) from {len(jobs)} source(s)",
                          outputs={"ingestion": res}, metrics={"stored": stored, "sources": len(jobs)},
                          started_at=started, ended_at=_utcnow())


# ---- HERALD (evidence) — notable safe news → monitor-grade evidence ----

class HeraldDesk(EvidenceDesk):
    desk_id = "herald"

    def analyze(self, dbs: CamelDbs, ctx: Optional[Dict] = None) -> List[EvidenceObject]:
        with connection(dbs.news) as conn:
            rows = [dict(r) for r in conn.execute(
                "SELECT title, severity, direction, confidence, affected_assets, event_date "
                "FROM news_events WHERE safe=1 AND severity IS NOT NULL ORDER BY id DESC LIMIT 20")]
        out: List[EvidenceObject] = []
        for r in rows:
            if (r.get("severity") or 0) < 2:                 # only notable events become evidence
                continue
            try:
                assets = json.loads(r.get("affected_assets") or "[]")
            except (ValueError, TypeError):
                assets = []
            direction = r.get("direction") if r.get("direction") in ("positive", "negative", "neutral") else "neutral"
            out.append(EvidenceObject(
                desk=self.desk_id, claim=f"news: {(r.get('title') or '')[:120]}",
                scope=(assets[0] if assets else "market"), source_count=1,
                freshness=r.get("event_date") or "recent", confidence=float(r.get("confidence") or 0.4),
                direction=direction, invalidation_conditions="event superseded / retracted",
                recommended_action="monitor", portfolio_fit="any", compliance_status="n/a"))
        return out


# ---- ORACLE (evidence) — macro regime; delegates to the existing MacroDesk ----

class OracleDesk(EvidenceDesk):
    desk_id = "oracle"

    def analyze(self, dbs: CamelDbs, ctx: Optional[Dict] = None) -> List[EvidenceObject]:
        from research.desks import MacroDesk
        notes = MacroDesk().analyze(dbs, ctx)
        for n in notes:
            n.desk = self.desk_id
        return notes


# ---- MUFTI (evidence) — Sharia compliance; delegates to the existing ShariaDesk (priority #1) ----

class MuftiDesk(EvidenceDesk):
    desk_id = "mufti"

    def analyze(self, dbs: CamelDbs, ctx: Optional[Dict] = None) -> List[EvidenceObject]:
        from research.desks import ShariaDesk
        notes = ShariaDesk().analyze(dbs, ctx)
        for n in notes:
            n.desk = self.desk_id
        return notes


# ---- QUANT (evidence) — the 17-check Edge Proof per whitelisted name ----

class QuantDesk(EvidenceDesk):
    desk_id = "quant"

    def analyze(self, dbs: CamelDbs, ctx: Optional[Dict] = None) -> List[EvidenceObject]:
        ctx = ctx or {}
        symbols = ctx.get("symbols") or _whitelist_symbols(dbs)
        from trader.engine.edge_proof import evaluate_signal_full
        out: List[EvidenceObject] = []
        for sym in symbols[:10]:
            try:
                rep = evaluate_signal_full(dbs, sym, signal="workforce",
                                           signal_definition="desk:quant", mode="enforcing")
            except Exception:                                # a symbol with no/thin data → skip, not crash
                continue
            allowed = bool(getattr(rep, "trade_allowed", False))
            hit = float(getattr(rep, "hit_rate", 0.0) or 0.0)
            n = int(getattr(rep, "sample_size", 0) or 0)
            out.append(EvidenceObject(
                desk=self.desk_id,
                claim=f"{sym} edge {'CONFIRMED' if allowed else 'none'} (hit_rate={hit:.0%}, n={n})",
                scope=sym, source_count=2, freshness="latest prices", confidence=hit,
                direction="positive" if allowed else "neutral",
                invalidation_conditions=(getattr(rep, "reason", "") or "edge decays"),
                recommended_action="propose buy (edge proven)" if allowed else "no edge → DCA core",
                portfolio_fit="core_sharia_growth", compliance_status="n/a"))
        return out


# ---- STEWARD (operator) — portfolio read-only summary (governed exits run in the tick) ----

class StewardDesk(OperatorDesk):
    desk_id = "steward"

    def run(self, dbs: CamelDbs, ctx: Optional[Dict] = None) -> DeskResult:
        started = _utcnow()
        from broker.positions import all_positions
        positions = all_positions(dbs.portfolio)
        with connection(dbs.portfolio) as conn:
            row = conn.execute("SELECT balance_after FROM ledger ORDER BY id DESC LIMIT 1").fetchone()
        cash = float(row[0]) if row and row[0] is not None else 0.0
        pos_val = sum(p.market_value for p in positions)
        fund = cash + pos_val
        outputs = {"cash": cash, "positions_value": pos_val, "fund": fund,
                   "positions": [{"symbol": p.symbol, "qty": p.qty, "market_value": p.market_value}
                                 for p in positions]}
        return DeskResult(self.desk_id, "ok" if (positions or cash > 0) else "empty",
                          summary=f"fund=${fund:,.2f} · {len(positions)} open position(s) · cash=${cash:,.2f}",
                          outputs=outputs, metrics={"fund": fund, "open_positions": len(positions), "cash": cash},
                          started_at=started, ended_at=_utcnow())


# ---- CONDUCTOR (operator) — assembles evidence; S17.6 turns this into the Opportunity Board ----

class ConductorDesk(OperatorDesk):
    desk_id = "conductor"

    def run(self, dbs: CamelDbs, ctx: Optional[Dict] = None) -> DeskResult:
        started = _utcnow()
        with connection(dbs.learning) as conn:
            n = conn.execute("SELECT COUNT(*) FROM research_evidence").fetchone()[0]
        # S17.1 readiness only — the CONDUCTOR is the SOLE buy path and remains fully gated; it builds NO
        # proposal here. S17.6 (opportunity_board) assembles the ranked, reasoned board from this evidence.
        return DeskResult(self.desk_id, "ok",
                          summary=f"{n} evidence note(s) available to assemble (board → S17.6)",
                          metrics={"evidence_available": n}, started_at=started, ended_at=_utcnow())

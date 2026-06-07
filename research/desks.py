"""
Vertical analyst desks (S12.5) — deterministic, evidence-only placeholders for the future Agent-SDK desks.

Two desks ship now (the gate requires ≥1): a Sharia auditor and a macro/regime desk. They read the
governed DBs and emit EvidenceObjects — they cannot act. When the real LLM desks arrive they replace
the `analyze` body and return the same contract; everything around them is already built.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection
from research.desk import AnalystDesk
from research.evidence import EvidenceObject


class ShariaDesk(AnalystDesk):
    desk_id = "sharia_auditor"

    def analyze(self, dbs: CamelDbs, context: Optional[Dict] = None) -> List[EvidenceObject]:
        out: List[EvidenceObject] = []
        with connection(dbs.sharia) as conn:
            rows = [dict(r) for r in conn.execute(
                "SELECT symbol, final_status, drift, confidence FROM sharia_status "
                "WHERE id IN (SELECT MAX(id) FROM sharia_status GROUP BY symbol)")]
        for r in rows:
            if r["final_status"] != "pass" or r["drift"]:
                out.append(EvidenceObject(
                    desk=self.desk_id,
                    claim=f"{r['symbol']} is not a clear Sharia pass ({r['final_status']}"
                          f"{', drift' if r['drift'] else ''})",
                    scope=r["symbol"], source_count=2, freshness="latest screen",
                    confidence=float(r["confidence"] or 0.5), direction="negative",
                    invalidation_conditions="a clean re-screen restores 'pass'",
                    recommended_action="freeze for new buys, reduce-only", portfolio_fit="any",
                    compliance_status=r["final_status"]))
        return out


class MacroDesk(AnalystDesk):
    desk_id = "macro_regime"

    def analyze(self, dbs: CamelDbs, context: Optional[Dict] = None) -> List[EvidenceObject]:
        with connection(dbs.macro) as conn:
            row = conn.execute(
                "SELECT regime, confidence, classified_at FROM regime_history ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return []
        risk_off = row["regime"] in ("RECESSION_RISK", "GEOPOLITICAL_RISK_OFF", "INFLATION_SHOCK")
        return [EvidenceObject(
            desk=self.desk_id,
            claim=f"macro regime is {row['regime']}",
            scope="portfolio", source_count=2, freshness=row["classified_at"] or "latest",
            confidence=float(row["confidence"] or 0.5),
            direction="negative" if risk_off else "neutral",
            invalidation_conditions="regime reclassification",
            recommended_action="tilt defensive" if risk_off else "stay the course",
            portfolio_fit="core_sharia_growth", compliance_status="n/a")]

"""
L3 — improvement proposer (S11). PROPOSE-ONLY: writes change requests for a human (L4) to approve.

The agent can never apply these — there is deliberately no agent-callable `apply()`. It writes to
`learning_proposals` (status='pending'); the founder approves/rejects out-of-band. L4 (the Constitution,
adding new strategies, and the weight band itself) is founder-only and has no code path here at all.
"""
from __future__ import annotations

import json
from typing import Dict, List, Optional

from db.paths import CamelDbs
from db.sqlite import connection


def propose(dbs: CamelDbs, proposal_type: str, *, strategy_id: Optional[str] = None,
            detail: Optional[Dict] = None, rationale: str = "") -> int:
    """Record a proposed change for founder review. Returns the proposal id. Never auto-applies."""
    with connection(dbs.learning) as conn:
        cur = conn.execute(
            "INSERT INTO learning_proposals (proposal_type, strategy_id, detail, rationale) "
            "VALUES (?,?,?,?)",
            (proposal_type, strategy_id, json.dumps(detail or {}), rationale),
        )
        return cur.lastrowid


def list_pending(dbs: CamelDbs) -> List[dict]:
    with connection(dbs.learning) as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM learning_proposals WHERE status='pending' ORDER BY id")]


def decide(dbs: CamelDbs, proposal_id: int, approve: bool, decided_by: str) -> None:
    """Founder-only resolution (L4). `decided_by` must be a human; recorded for the audit trail."""
    from datetime import datetime, timezone
    with connection(dbs.learning) as conn:
        conn.execute(
            "UPDATE learning_proposals SET status=?, decided_by=?, decided_at=? WHERE id=?",
            ("approved" if approve else "rejected", decided_by,
             datetime.now(timezone.utc).isoformat(), proposal_id),
        )

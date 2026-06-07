"""
Human approval gate (S13) — the one-tap approve/veto channel for live actions.

In Phase 1 every trade needs a human yes. This persists an approval request (pending) and resolves it on
a founder approve/veto (delivered via Telegram, S6). The assembled loop's phase-gated approval hook calls
`approval_fn(dbs)` — which defaults to **withholding** approval: an action is executed only after an
explicit, recorded human approval. Fail-safe: unknown / pending / vetoed → not approved.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from db.paths import CamelDbs
from db.sqlite import connection
from guardrail.constitution import Action


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def request_approval(dbs: CamelDbs, action_ref: str, *, channel: str = "telegram") -> int:
    with connection(dbs.portfolio) as conn:
        cur = conn.execute(
            "INSERT INTO approvals (action_ref, status, channel) VALUES (?, 'pending', ?)",
            (action_ref, channel))
        return cur.lastrowid


def decide(dbs: CamelDbs, action_ref: str, approve: bool, decided_by: str) -> None:
    """Founder-only. `decided_by` is recorded for the audit trail."""
    with connection(dbs.portfolio) as conn:
        conn.execute(
            "UPDATE approvals SET status=?, decided_at=?, decided_by=? WHERE action_ref=?",
            ("approved" if approve else "vetoed", _utcnow(), decided_by, action_ref))


def is_approved(dbs: CamelDbs, action_ref: str) -> bool:
    """True only for an explicit, recorded approval. Fail-safe: missing/pending/vetoed → False."""
    if not action_ref:
        return False
    with connection(dbs.portfolio) as conn:
        row = conn.execute(
            "SELECT status FROM approvals WHERE action_ref=? ORDER BY id DESC LIMIT 1",
            (action_ref,)).fetchone()
    return bool(row) and row["status"] == "approved"


def approval_fn(dbs: CamelDbs) -> Callable[[Action], bool]:
    """An approval callback for the assembled loop's phase-gated Human-Approval gate."""
    def _fn(action: Action) -> bool:
        return is_approved(dbs, getattr(action, "approval_id", None) or getattr(action, "symbol", ""))
    return _fn

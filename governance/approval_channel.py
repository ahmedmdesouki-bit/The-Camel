"""
Approval channel (S13) — the INBOUND side of the one-tap human-approval gate.

`governance/approval.py` records the request and resolves a decision; this parses a founder's reply
("approve <ref>" / "veto <ref>") and dispatches it to `decide`. The actual Telegram bot connection (a bot
token + long-poll/webhook) is the **paid/founder dependency (S15)** — but the command grammar + dispatch +
authorization are pure and fully testable here. Fail-safe: an unrecognised command, an unknown ref, or a
sender who is not the founder does **nothing** (never an accidental approval).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from db.paths import CamelDbs
from governance.approval import decide, is_approved

_APPROVE_WORDS = {"approve", "yes", "ok", "confirm", "/approve"}
_VETO_WORDS = {"veto", "no", "reject", "deny", "cancel", "/veto"}


@dataclass
class CommandResult:
    handled: bool
    action_ref: str = ""
    approved: Optional[bool] = None
    reply: str = ""


def parse_command(text: str):
    """('approve'|'veto', action_ref) or None. Tolerant of case, leading slash, and extra words."""
    if not text:
        return None
    toks = str(text).strip().split()
    if not toks:
        return None
    verb = toks[0].lower()
    ref = toks[1] if len(toks) > 1 else ""
    if verb in _APPROVE_WORDS and ref:
        return ("approve", ref)
    if verb in _VETO_WORDS and ref:
        return ("veto", ref)
    return None


def handle_command(dbs: CamelDbs, text: str, *, sender: str, founder_id: str) -> CommandResult:
    """Authorize the sender, parse the command, and record the decision. Founder-only; fail-safe to no-op."""
    if not founder_id or sender != founder_id:
        return CommandResult(handled=False, reply="unauthorized: only the founder can approve/veto")
    parsed = parse_command(text)
    if parsed is None:
        return CommandResult(handled=False, reply="usage: approve <ref> | veto <ref>")
    verb, ref = parsed
    approve = verb == "approve"
    decide(dbs, ref, approve, decided_by=sender)
    return CommandResult(handled=True, action_ref=ref, approved=approve,
                         reply=f"{'APPROVED' if approve else 'VETOED'} {ref}"
                               + (" — will execute on the next tick." if approve and is_approved(dbs, ref)
                                  else " — withheld."))

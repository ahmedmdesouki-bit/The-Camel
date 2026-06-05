"""
Tool Permission Matrix (S4) — what each tool may do, what needs approval, what is forbidden.

Every tool action routes through `evaluate_tool_action(tool, action, state)`. Default-deny:
an unknown tool or an unlisted action is rejected. Forbidden actions are rejected outright;
approval-gated actions are allowed only with `approval_id` (or flagged requires_approval).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional, Set

# tool -> {allowed, approval, forbidden} sets of action keywords (lowercased)
MATRIX: Dict[str, Dict[str, Set[str]]] = {
    "github": {
        "allowed":   {"branch", "commit", "open_pr", "read"},
        "approval":  {"merge_main"},
        "forbidden": {"delete_repo"},
    },
    "supabase": {
        "allowed":   {"read", "write_app_db"},
        "approval":  {"schema_migration"},
        "forbidden": {"delete_tables"},
    },
    "netlify": {
        "allowed":   {"deploy_preview"},
        "approval":  {"production_deploy"},
        "forbidden": {"delete_domain", "delete_dns"},
    },
    "playwright": {
        "allowed":   {"browse", "scrape", "qa"},
        "approval":  {"submit_nonfinancial_form"},
        "forbidden": {"broker_action", "move_money", "change_account",
                      "change_margin", "change_whitelist", "change_approval"},
    },
    "broker": {
        "allowed":   {"paper_trade"},
        "approval":  {"live_order"},
        "forbidden": {"withdraw", "margin", "options"},
    },
    "telegram": {
        "allowed":   {"send_alert"},
        "approval":  {"approval_confirmation"},
        "forbidden": {"change_rules"},
    },
}


@dataclass
class ToolDecision:
    allow: bool
    requires_approval: bool
    reason: str


def evaluate_tool_action(
    tool: str,
    action: str,
    approval_id: Optional[str] = None,
) -> ToolDecision:
    """
    Decide whether `tool` may perform `action`. Default-deny for unknown tool/action.
    Approval-gated actions are allowed only when an approval_id is supplied.
    """
    t = (tool or "").lower()
    a = (action or "").lower()
    spec = MATRIX.get(t)
    if spec is None:
        return ToolDecision(False, False, f"Unknown tool '{tool}' — default deny.")

    if a in spec["forbidden"]:
        return ToolDecision(False, False, f"'{action}' is forbidden for {tool}.")
    if a in spec["approval"]:
        if approval_id:
            return ToolDecision(True, True, f"'{action}' approved ({approval_id}).")
        return ToolDecision(False, True, f"'{action}' on {tool} requires founder approval.")
    if a in spec["allowed"]:
        return ToolDecision(True, False, f"'{action}' allowed for {tool}.")
    return ToolDecision(False, False, f"'{action}' not listed for {tool} — default deny.")

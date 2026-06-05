"""
S4 — governance tests: config immutability + tool permission matrix.
"""
import pytest
from governance.config_guard import (
    ConfigImmutableError, agent_write_config, is_founder_owned, find_writable_founder_config,
)
from governance.tool_permissions import evaluate_tool_action


# ---------------- config immutability (proves Constitution rule #7) ----------------

def test_agent_cannot_write_config():
    with pytest.raises(ConfigImmutableError):
        agent_write_config("config/limits.yaml", {"max_position_pct": 0.99})

def test_agent_cannot_write_whitelist_config():
    with pytest.raises(ConfigImmutableError):
        agent_write_config("whitelist", "anything")

def test_is_founder_owned_recognises_limits():
    assert is_founder_owned("config/limits.yaml")
    assert is_founder_owned("tool_permissions")
    assert is_founder_owned("approval_thresholds")

def test_is_founder_owned_false_for_app_data():
    assert not is_founder_owned("noah_market.db")
    assert not is_founder_owned("some_random_file.txt")

def test_find_writable_founder_config_ignores_nonexistent():
    # a founder-owned path that does not exist on disk → not a violation
    assert find_writable_founder_config(["nonexistent_budget_config.yaml"]) == []

def test_find_writable_flags_existing_writable_config():
    # The real config IS OS-writable on a dev box (locking it read-only to the agent user is
    # a founder machine-hardening step, S6). The helper must FLAG it so the founder can act.
    import os
    if os.path.exists("config/limits.yaml") and os.access("config/limits.yaml", os.W_OK):
        assert "config/limits.yaml" in find_writable_founder_config(["config/limits.yaml"])


# ---------------- tool permission matrix ----------------

def test_github_commit_allowed():
    d = evaluate_tool_action("github", "commit")
    assert d.allow and not d.requires_approval

def test_github_delete_repo_forbidden():
    d = evaluate_tool_action("github", "delete_repo")
    assert not d.allow

def test_github_merge_main_needs_approval():
    assert not evaluate_tool_action("github", "merge_main").allow
    assert evaluate_tool_action("github", "merge_main", approval_id="appr_1").allow

def test_playwright_broker_action_forbidden():
    d = evaluate_tool_action("playwright", "broker_action")
    assert not d.allow and "forbidden" in d.reason.lower()

def test_broker_live_order_needs_approval():
    assert not evaluate_tool_action("broker", "live_order").allow
    assert evaluate_tool_action("broker", "live_order", approval_id="appr_2").allow

def test_broker_withdraw_forbidden():
    assert not evaluate_tool_action("broker", "withdraw").allow

def test_broker_paper_trade_allowed():
    assert evaluate_tool_action("broker", "paper_trade").allow

def test_unknown_tool_default_deny():
    assert not evaluate_tool_action("mystery_tool", "anything").allow

def test_unknown_action_default_deny():
    assert not evaluate_tool_action("github", "rewrite_history").allow

def test_telegram_change_rules_forbidden():
    assert not evaluate_tool_action("telegram", "change_rules").allow

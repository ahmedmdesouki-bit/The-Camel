"""
Config immutability guard (S4) — proves Constitution rule #7 in code, not just words.

The founder-owned config (limits, whitelist rules, tool permissions, budget, approval
thresholds) must be unwritable by the agent process. We enforce this at the code level:
the agent has NO function that writes founder config — the only writer is the founder,
out-of-band. Any agent-side attempt routes here and raises.

A best-effort OS read-only check (`os_writable`) is also provided for the founder to wire
into startup, but the code-level refusal below is the invariant the test suite proves.
"""
from __future__ import annotations
import os
from typing import List

# Names/paths that only the founder may change.
FOUNDER_OWNED = (
    "config/limits.yaml",
    "whitelist",
    "tool_permissions",
    "budget",
    "approval_thresholds",
    "sharia_rules",
)


class ConfigImmutableError(RuntimeError):
    """Raised when the agent process attempts to write founder-owned config."""


def is_founder_owned(name: str) -> bool:
    """True if `name` refers to founder-owned config the agent may not write."""
    n = (name or "").lower().replace("\\", "/")
    return any(token in n for token in FOUNDER_OWNED)


def agent_write_config(target: str, *_args, **_kwargs) -> None:
    """
    The ONLY config-write entry point reachable from agent code. It always refuses —
    there is deliberately no path for the agent to mutate founder-owned config.
    Constitution rule #7: "Noah cannot change its own rules."
    """
    raise ConfigImmutableError(
        f"Agent process cannot write founder-owned config ({target!r}). "
        "Constitution rule #7 — change limits deliberately, out-of-band, as the founder."
    )


def os_writable(path: str) -> bool:
    """
    Best-effort: is `path` writable by the current process at the OS level?
    Founder wires this into startup to assert the config file is OS read-only to the
    agent user. Returns False if the path does not exist (nothing to write).
    """
    if not os.path.exists(path):
        return False
    return os.access(path, os.W_OK)


def find_writable_founder_config(paths: List[str]) -> List[str]:
    """Return any founder-owned paths that are OS-writable (a hardening violation)."""
    return [p for p in paths if is_founder_owned(p) and os_writable(p)]

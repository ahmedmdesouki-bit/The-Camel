"""
Secrets exposure startup check (S5.5).

Phase 0 keeps secrets in .env (plaintext) — acceptable, but the operator should KNOW it and
flag it. S6 adds the hard refusal once a secrets manager exists. This check warns when a
sensitive key is present as a real (non-placeholder) plaintext env var.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

SENSITIVE_KEYS = (
    "ALPACA_API_KEY", "ALPACA_API_SECRET",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "SUPABASE_SERVICE_KEY",
)


def is_placeholder(value: str) -> bool:
    """A value counts as a placeholder/empty (not a real secret)."""
    v = (value or "").strip()
    return (not v) or "your_" in v.lower() or v.lower() in ("true", "false") or len(v) < 8


@dataclass
class SecretsReport:
    clean: bool
    plaintext_keys: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


def scan_plaintext_env(env: Dict[str, str], keys=SENSITIVE_KEYS) -> List[str]:
    """Return sensitive keys that are set to a real (non-placeholder) value."""
    return [k for k in keys if not is_placeholder(env.get(k, ""))]


def check_startup(env: Optional[Dict[str, str]] = None) -> SecretsReport:
    env = dict(os.environ if env is None else env)
    plaintext = scan_plaintext_env(env)
    warnings = [
        f"{k} is set as a plaintext env var — move to Windows Credential Manager (S6)."
        for k in plaintext
    ]
    return SecretsReport(clean=len(plaintext) == 0, plaintext_keys=plaintext, warnings=warnings)

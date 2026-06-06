"""
Secrets manager (S6) — credential interface + the HARD plaintext refusal.

Reads secrets from the OS credential store (Windows Credential Manager via `keyring` if
installed) and falls back to env in Phase 0. S6 adds the hard refusal: in strict mode,
startup RAISES if a sensitive key is sitting in a plaintext env var — extending the S5.5
warn-only scan into an enforced gate.
"""
from __future__ import annotations
import os
from typing import Optional

from ops.secrets_check import SENSITIVE_KEYS, scan_plaintext_env


class PlaintextSecretError(RuntimeError):
    """Raised in strict mode when a sensitive key is present as a plaintext env var."""


def get_secret(name: str) -> Optional[str]:
    """OS credential store first (keyring), then env (Phase 0 fallback)."""
    try:
        import keyring  # optional dependency
        val = keyring.get_password("the-camel", name)
        if val:
            return val
    except Exception:
        pass
    return os.environ.get(name)


def store_secret(name: str, value: str) -> bool:
    """Store in the OS credential store. Returns False if keyring is unavailable."""
    try:
        import keyring
        keyring.set_password("the-camel", name, value)
        return True
    except Exception:
        return False


def enforce_startup(env: Optional[dict] = None, strict: bool = True) -> list:
    """
    Check for plaintext sensitive secrets. In strict mode (S6 default) RAISE on any finding;
    otherwise return the list of offending keys (warn-only, S5.5 behaviour).
    """
    env = dict(os.environ if env is None else env)
    offenders = scan_plaintext_env(env, SENSITIVE_KEYS)
    if offenders and strict:
        raise PlaintextSecretError(
            "Plaintext secrets in env: " + ", ".join(offenders) +
            " — store them in the OS credential store (the-camel) instead."
        )
    return offenders

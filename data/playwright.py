"""
Playwright adapter — STUB (S4).

Enforces the Tool Permission Matrix in code: Playwright may be used (later) for scraping,
QA, and reading public data — but NEVER for broker actions, money movement, or changing
account / margin / whitelist / approval settings. Every entry point raises until the real
scraping adapter is wired in a later sprint.
"""
from __future__ import annotations


class PlaywrightForbiddenError(NotImplementedError):
    """Raised for any forbidden or not-yet-implemented Playwright action."""


def fetch(url: str, *_args, **_kwargs):
    raise PlaywrightForbiddenError(
        "Playwright scraping is not implemented yet (wired in a later sprint for "
        "public-data / QA use only)."
    )


def submit_broker_action(*_args, **_kwargs):
    raise PlaywrightForbiddenError(
        "FORBIDDEN: Playwright may never place broker orders or move money "
        "(Tool Permission Matrix). Use the broker API behind the Constitution + approval gate."
    )


def change_settings(*_args, **_kwargs):
    raise PlaywrightForbiddenError(
        "FORBIDDEN: Playwright may never change account / margin / whitelist / approval "
        "settings (Tool Permission Matrix)."
    )

"""
LiveBroker (S13) — the autonomous live path (Alpaca), GATED OFF and fail-safe.

This is the Phase-2 auto-execution path. It is deliberately inert by default: `submit` REFUSES unless
ALL of three founder-owned conditions hold — phase ≥ 1, an explicit `live_enabled` flag, and trade-only
credentials present. Even when all three are set, the real Alpaca integration is not wired (no broker
credentials live in the repo), so it raises rather than silently trading. There is no configuration in
which this class moves real money on its own — flipping to live capital is a deliberate human act.
"""
from __future__ import annotations

from typing import Optional

from guardrail.constitution import Action, Decision


class LiveTradingDisabled(Exception):
    """Raised when a live order is attempted while live trading is not fully + explicitly enabled."""


class LiveBroker:
    def __init__(self, *, phase: int = 0, live_enabled: bool = False,
                 credentials: Optional[dict] = None):
        self.phase = phase
        self.live_enabled = live_enabled        # the deliberate founder switch — defaults OFF
        self.credentials = credentials          # trade-only, withdrawals disabled (never in the repo)

    def _gate(self) -> None:
        if self.phase < 1:
            raise LiveTradingDisabled("Phase 0 — live trading is disabled (paper only)")
        if not self.live_enabled:
            raise LiveTradingDisabled("live_enabled flag not set by the founder — refusing")
        if not self.credentials:
            raise LiveTradingDisabled("no trade-only broker credentials — refusing")

    def submit(self, action: Action, decision: Decision):
        self._gate()                            # default path always raises here (fail-safe)
        # Even fully enabled, the real integration is Phase-2 work and is intentionally not wired.
        raise NotImplementedError(
            "LiveBroker gate passed, but the Alpaca live integration is Phase-2 and not wired "
            "(no credentials in the repo). Implement against a trade-only key before going live.")

"""
LiveBroker stub — Phase 1+ only.
Raises NotImplementedError in Phase 0; wired behind a feature flag.
"""
from guardrail.constitution import Action, Decision


class LiveBroker:
    def submit(self, action: Action, decision: Decision):
        raise NotImplementedError(
            "LiveBroker is disabled in Phase 0. "
            "Set NOAH_PHASE >= 1 and implement the Approval Channel first."
        )

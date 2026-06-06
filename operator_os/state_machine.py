"""
Operator State Machine (S5) — Camel is not a loose loop.

Eleven formal states with explicit, enforced transitions. The key safety rules:
  - cannot jump FORMING_THESIS -> ACTING (must prove edge + get approval first)
  - ACTING is reachable ONLY from AWAITING_APPROVAL (no acting without the gate)
  - cannot leave PAUSED without founder approval
  - KILLED is terminal — only a manual restart() returns to IDLE
"""
from __future__ import annotations
from enum import Enum
from typing import Dict, Set


class State(str, Enum):
    IDLE = "IDLE"
    OBSERVING = "OBSERVING"
    RESEARCHING = "RESEARCHING"
    FORMING_THESIS = "FORMING_THESIS"
    TESTING_EDGE = "TESTING_EDGE"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    ACTING = "ACTING"
    MONITORING = "MONITORING"
    LEARNING = "LEARNING"
    PAUSED = "PAUSED"
    KILLED = "KILLED"


# Allowed forward transitions (PAUSED and KILLED are reachable from anywhere via pause()/kill()).
ALLOWED: Dict[State, Set[State]] = {
    State.IDLE:              {State.OBSERVING},
    State.OBSERVING:         {State.RESEARCHING, State.IDLE},
    State.RESEARCHING:       {State.FORMING_THESIS, State.OBSERVING},
    State.FORMING_THESIS:    {State.TESTING_EDGE, State.RESEARCHING},   # NOT ACTING
    State.TESTING_EDGE:      {State.AWAITING_APPROVAL, State.FORMING_THESIS, State.IDLE},
    State.AWAITING_APPROVAL: {State.ACTING, State.IDLE},                # ACTING only from here
    State.ACTING:            {State.MONITORING},
    State.MONITORING:        {State.LEARNING, State.OBSERVING},
    State.LEARNING:          {State.IDLE, State.OBSERVING},
    State.PAUSED:            {State.IDLE, State.OBSERVING},             # only with founder approval
    State.KILLED:            set(),                                     # terminal
}


class InvalidTransition(RuntimeError):
    pass


class StateMachine:
    def __init__(self, state: State = State.IDLE):
        self.state = state
        self._paused_from: State | None = None

    def can(self, to: State) -> bool:
        if self.state == State.KILLED:
            return False
        return to in ALLOWED[self.state]

    def transition(self, to: State, founder_approval: bool = False) -> State:
        if self.state == State.KILLED:
            raise InvalidTransition("KILLED is terminal — use restart().")
        if self.state == State.PAUSED and not founder_approval:
            raise InvalidTransition("Leaving PAUSED requires founder approval.")
        if to not in ALLOWED[self.state]:
            raise InvalidTransition(f"{self.state.value} -> {to.value} is not allowed.")
        self.state = to
        return self.state

    def pause(self) -> State:
        """Pause is allowed from any non-terminal state."""
        if self.state == State.KILLED:
            raise InvalidTransition("Cannot pause a KILLED operator.")
        self._paused_from = self.state
        self.state = State.PAUSED
        return self.state

    def kill(self) -> State:
        """Kill is allowed from any state and is terminal."""
        self.state = State.KILLED
        return self.state

    def restart(self) -> State:
        """Only a KILLED operator can be manually restarted, back to IDLE."""
        if self.state != State.KILLED:
            raise InvalidTransition("restart() only applies to a KILLED operator.")
        self.state = State.IDLE
        self._paused_from = None
        return self.state

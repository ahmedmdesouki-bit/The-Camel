"""
S5 — Operator State Machine tests.
"""
import pytest
from operator_os.state_machine import State, StateMachine, InvalidTransition


def test_happy_path_full_cycle():
    m = StateMachine()
    for s in (State.OBSERVING, State.RESEARCHING, State.FORMING_THESIS,
              State.TESTING_EDGE, State.AWAITING_APPROVAL, State.ACTING,
              State.MONITORING, State.LEARNING, State.IDLE):
        m.transition(s)
    assert m.state == State.IDLE


def test_cannot_jump_forming_thesis_to_acting():
    m = StateMachine(State.FORMING_THESIS)
    with pytest.raises(InvalidTransition):
        m.transition(State.ACTING)

def test_acting_only_from_awaiting_approval():
    # reachable from AWAITING_APPROVAL
    assert StateMachine(State.AWAITING_APPROVAL).transition(State.ACTING) == State.ACTING
    # not reachable from TESTING_EDGE or MONITORING
    with pytest.raises(InvalidTransition):
        StateMachine(State.TESTING_EDGE).transition(State.ACTING)
    with pytest.raises(InvalidTransition):
        StateMachine(State.MONITORING).transition(State.ACTING)

def test_cannot_skip_edge_proof_path():
    # OBSERVING cannot go straight to ACTING
    with pytest.raises(InvalidTransition):
        StateMachine(State.OBSERVING).transition(State.ACTING)


# ---------------- pause / kill / restart ----------------

def test_pause_from_any_state():
    m = StateMachine(State.MONITORING)
    assert m.pause() == State.PAUSED

def test_cannot_leave_paused_without_approval():
    m = StateMachine(State.OBSERVING)
    m.pause()
    with pytest.raises(InvalidTransition):
        m.transition(State.OBSERVING)                      # no approval
    assert m.transition(State.OBSERVING, founder_approval=True) == State.OBSERVING

def test_kill_is_terminal():
    m = StateMachine(State.ACTING)
    m.kill()
    assert m.state == State.KILLED
    with pytest.raises(InvalidTransition):
        m.transition(State.MONITORING)
    with pytest.raises(InvalidTransition):
        m.pause()

def test_restart_only_from_killed():
    m = StateMachine(State.IDLE)
    with pytest.raises(InvalidTransition):
        m.restart()
    m.kill()
    assert m.restart() == State.IDLE

def test_can_helper():
    m = StateMachine(State.FORMING_THESIS)
    assert m.can(State.TESTING_EDGE)
    assert not m.can(State.ACTING)
    m.kill()
    assert not m.can(State.IDLE)

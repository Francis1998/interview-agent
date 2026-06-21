"""Tests for RunStateMachine."""

import pytest

from interview_agent.lifecycle.state_machine import InvalidTransitionError, RunStateMachine
from interview_agent.models import RunState


@pytest.fixture
def sm() -> RunStateMachine:
    return RunStateMachine()


def test_valid_happy_path(sm: RunStateMachine) -> None:
    """Full lifecycle transitions should be valid."""
    path = [
        RunState.IDLE,
        RunState.PLANNING,
        RunState.RETRIEVING,
        RunState.REASONING,
        RunState.ANSWERING,
        RunState.DONE,
    ]
    for i in range(len(path) - 1):
        assert sm.can_transition(path[i], path[i + 1])


def test_invalid_skip_planning(sm: RunStateMachine) -> None:
    """Skipping PLANNING should raise."""
    with pytest.raises(InvalidTransitionError):
        sm.validate(RunState.IDLE, RunState.REASONING)


def test_terminal_states(sm: RunStateMachine) -> None:
    """Terminal states have no outgoing transitions."""
    for state in RunStateMachine.TERMINAL:
        assert sm.next_states(state) == set()

"""Explicit state transition validation for agent runs."""

from typing import ClassVar

from interview_agent.models import RunState


class InvalidTransitionError(ValueError):
    """Raised when an agent run attempts an invalid state transition."""


class RunStateMachine:
    """Validate the IDLE-to-DONE/CANCELLED/ERROR state machine."""

    _allowed: ClassVar[dict[RunState, set[RunState]]] = {
        RunState.IDLE: {RunState.PLANNING, RunState.ERROR, RunState.CANCELLED},
        RunState.PLANNING: {RunState.RETRIEVING, RunState.ERROR, RunState.CANCELLED},
        RunState.RETRIEVING: {RunState.REASONING, RunState.ERROR, RunState.CANCELLED},
        RunState.REASONING: {RunState.ANSWERING, RunState.ERROR, RunState.CANCELLED},
        RunState.ANSWERING: {RunState.DONE, RunState.ERROR, RunState.CANCELLED},
        RunState.DONE: set(),
        RunState.ERROR: set(),
        RunState.CANCELLED: set(),
    }

    TERMINAL: ClassVar[set[RunState]] = {RunState.DONE, RunState.ERROR, RunState.CANCELLED}

    def can_transition(self, from_state: RunState, to_state: RunState) -> bool:
        """Return whether a transition is valid."""
        return to_state in self._allowed[from_state]

    def validate(self, from_state: RunState, to_state: RunState) -> None:
        """Raise when a transition is not part of the explicit state machine."""
        if not self.can_transition(from_state, to_state):
            message = f"invalid state transition: {from_state.value} -> {to_state.value}"
            raise InvalidTransitionError(message)

    def next_states(self, from_state: RunState) -> set[RunState]:
        """Return valid next states from the given state."""
        return set(self._allowed[from_state])

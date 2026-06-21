"""Tests for SafetyGuard."""

import pytest

from interview_agent.config import Settings
from interview_agent.safety.guard import RunCancelledError, SafetyGuard, ScopeViolationError


def test_empty_question_rejected() -> None:
    guard = SafetyGuard(Settings())
    with pytest.raises(ScopeViolationError):
        guard.validate_question("  ", "python")


def test_topic_allowlist() -> None:
    guard = SafetyGuard(Settings())
    with pytest.raises(ScopeViolationError):
        guard.validate_question("test", "blockchain")


def test_cancellation() -> None:
    guard = SafetyGuard(Settings())
    guard.cancel_run("run-123")
    with pytest.raises(RunCancelledError):
        guard.check_cancelled("run-123")

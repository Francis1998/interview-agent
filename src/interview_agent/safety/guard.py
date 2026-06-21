"""Safety controls — scope, timeout, cancellation."""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

import structlog

from interview_agent.config import Settings

logger = structlog.get_logger(__name__)

T = TypeVar("T")


class ScopeViolationError(PermissionError):
    """Raised when input exceeds allowed scope."""


class RunCancelledError(asyncio.CancelledError):
    """Raised when a run is cancelled by user or system."""


class SafetyGuard:
    """Enforce bounded scope, timeouts, and cancellation."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cancelled_runs: set[str] = set()

    def validate_question(self, question: str, topic: str) -> None:
        """Ensure question and topic are within allowed bounds."""
        if not question.strip():
            raise ScopeViolationError("Question cannot be empty.")
        if len(question) > 2000:
            raise ScopeViolationError("Question exceeds 2000 character limit.")
        if topic.lower() not in self._settings.topic_allowlist:
            raise ScopeViolationError(
                f"Topic '{topic}' not in allowlist: {sorted(self._settings.topic_allowlist)}"
            )

    def validate_tool_budget(self, tool_calls: int) -> None:
        if tool_calls >= self._settings.max_tool_calls:
            raise ScopeViolationError(
                f"Tool call budget exceeded ({self._settings.max_tool_calls})."
            )

    def cancel_run(self, run_id: str) -> None:
        self._cancelled_runs.add(run_id)
        logger.info("run_cancelled", run_id=run_id)

    def is_cancelled(self, run_id: str) -> bool:
        return run_id in self._cancelled_runs

    def check_cancelled(self, run_id: str) -> None:
        if self.is_cancelled(run_id):
            raise RunCancelledError(f"Run {run_id} was cancelled.")

    async def with_timeout(self, coro: Coroutine[Any, Any, T]) -> T:
        """Wrap coroutine with configured run timeout."""
        return await asyncio.wait_for(coro, timeout=self._settings.run_timeout_seconds)

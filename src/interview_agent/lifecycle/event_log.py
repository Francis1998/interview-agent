"""Durable event log — file-backed JSONL plus in-memory buffer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from interview_agent.models import EventType, RunEvent

logger = structlog.get_logger(__name__)


class EventLog:
    """Append-only durable event log per run."""

    def __init__(self, log_dir: Path) -> None:
        self._log_dir = log_dir
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._buffer: dict[str, list[RunEvent]] = {}

    def _path(self, run_id: str) -> Path:
        return self._log_dir / f"{run_id}.jsonl"

    async def append(self, event: RunEvent) -> None:
        """Append an event to memory and disk."""
        self._buffer.setdefault(event.run_id, []).append(event)
        line = event.model_dump_json() + "\n"
        path = self._path(event.run_id)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)
        logger.debug("event_appended", run_id=event.run_id, type=event.event_type.value)

    async def get_events(self, run_id: str) -> list[RunEvent]:
        """Return all events for a run, loading from disk if needed."""
        if run_id in self._buffer:
            return list(self._buffer[run_id])
        path = self._path(run_id)
        if not path.exists():
            return []
        events: list[RunEvent] = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    events.append(RunEvent.model_validate(json.loads(line)))
        self._buffer[run_id] = events
        return events

    async def emit(
        self,
        run_id: str,
        event_type: EventType,
        payload: dict[str, Any] | None = None,
    ) -> RunEvent:
        """Create and persist a new event."""
        event = RunEvent(run_id=run_id, event_type=event_type, payload=payload or {})
        await self.append(event)
        return event

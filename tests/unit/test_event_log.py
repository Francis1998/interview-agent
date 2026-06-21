"""Tests for EventLog."""

import pytest

from interview_agent.lifecycle.event_log import EventLog
from interview_agent.models import EventType


@pytest.mark.asyncio
async def test_append_and_load(tmp_path) -> None:
    """Events should persist to JSONL and reload."""
    log = EventLog(tmp_path)
    run_id = "test-run-1"
    await log.emit(run_id, EventType.RUN_STARTED, {"q": "hello"})
    await log.emit(run_id, EventType.RUN_COMPLETED, {"state": "done"})
    events = await log.get_events(run_id)
    assert len(events) == 2
    assert events[0].event_type == EventType.RUN_STARTED
    assert (tmp_path / f"{run_id}.jsonl").exists()

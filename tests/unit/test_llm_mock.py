"""Tests for LLM mock adapter."""

import pytest

from interview_agent.llm.mock_adapter import MockAdapter
from interview_agent.models import ChatMessage


@pytest.mark.asyncio
async def test_mock_complete() -> None:
    adapter = MockAdapter()
    response = await adapter.complete(
        "mock-interview-v1",
        [ChatMessage(role="user", content="Explain TCP three-way handshake")],
    )
    assert response.provider == "mock"
    assert "Interview Answer" in response.content
    assert await adapter.health_check()

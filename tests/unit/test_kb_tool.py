"""Tests for InterviewKBTool."""

import pytest

from interview_agent.tools.interview_kb import InterviewKBTool


@pytest.mark.asyncio
async def test_kb_search_by_keywords(knowledge_dir) -> None:
    """Keyword search should return matching sections."""
    tool = InterviewKBTool(knowledge_dir)
    result = await tool.invoke(topic="python", keywords="gil,thread")
    assert result.success
    assert "GIL" in result.output or "gil" in result.output.lower()


@pytest.mark.asyncio
async def test_kb_missing_topic(knowledge_dir) -> None:
    """Missing topic file should fail gracefully."""
    tool = InterviewKBTool(knowledge_dir)
    result = await tool.invoke(topic="nonexistent", keywords="")
    assert not result.success

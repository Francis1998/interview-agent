"""Integration test for full agent run (mock LLM)."""

import pytest

from interview_agent.agent.runner import AgentRunner
from interview_agent.config import Settings
from interview_agent.lifecycle.event_log import EventLog
from interview_agent.llm.router import LLMRouter
from interview_agent.models import AgentRunRequest, RunState
from interview_agent.tools.interview_kb import InterviewKBTool
from interview_agent.tools.registry import ToolRegistry


@pytest.fixture
def runner(tmp_path, knowledge_dir) -> AgentRunner:
    settings = Settings(
        event_log_dir=tmp_path / "events",
        knowledge_dir=knowledge_dir,
    )
    event_log = EventLog(settings.event_log_dir)
    tools = ToolRegistry()
    tools.register(InterviewKBTool(knowledge_dir))
    return AgentRunner(settings, event_log, tools, LLMRouter(settings))


@pytest.mark.asyncio
async def test_full_run_mock(runner: AgentRunner) -> None:
    """End-to-end run should complete with mock provider."""
    result = await runner.run(
        AgentRunRequest(question="What is the Python GIL?", topic_hint="python")
    )
    assert result.state == RunState.DONE
    assert result.answer
    assert result.topic == "python"
    assert len(result.rationale_traces) >= 3
    assert len(result.events) >= 5

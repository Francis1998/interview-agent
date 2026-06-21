"""Tests for DecisionEngine."""

from interview_agent.config import Settings
from interview_agent.decision.engine import DecisionEngine
from interview_agent.models import AgentRunRequest


def test_classify_python_topic() -> None:
    """Keyword scoring should pick python topic."""
    engine = DecisionEngine(Settings())
    req = AgentRunRequest(question="Explain the Python GIL and its impact on threading")
    trace = engine.classify_topic(req)
    assert trace.chosen == "python"
    assert trace.signals["method"] == "keyword_scoring"


def test_explicit_topic_hint() -> None:
    """Explicit hint should override keyword scoring."""
    engine = DecisionEngine(Settings())
    req = AgentRunRequest(question="How does it work?", topic_hint="redis")
    trace = engine.classify_topic(req)
    assert trace.chosen == "redis"
    assert trace.signals["method"] == "explicit_hint"


def test_mock_provider_when_no_keys() -> None:
    """Without API keys, provider should fall back to mock."""
    engine = DecisionEngine(Settings())
    req = AgentRunRequest(question="TCP handshake?")
    trace = engine.select_provider(req)
    assert trace.chosen == "mock"

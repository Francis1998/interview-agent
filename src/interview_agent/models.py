"""Core domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class RunState(str, Enum):
    """Agent run lifecycle states."""

    IDLE = "idle"
    PLANNING = "planning"
    RETRIEVING = "retrieving"
    REASONING = "reasoning"
    ANSWERING = "answering"
    DONE = "done"
    ERROR = "error"
    CANCELLED = "cancelled"


class EventType(str, Enum):
    """Durable event log entry types."""

    RUN_STARTED = "run_started"
    STATE_TRANSITION = "state_transition"
    DECISION = "decision"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    SAFETY_CHECK = "safety_check"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    RUN_CANCELLED = "run_cancelled"


class ChatMessage(BaseModel):
    """Normalized chat message for LLM adapters."""

    role: str
    content: str


class LLMResponse(BaseModel):
    """Normalized LLM completion response."""

    provider: str
    model: str
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


class DecisionRationale(BaseModel):
    """Trace record for a deterministic decision."""

    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    step: str
    chosen: str
    alternatives: list[str] = Field(default_factory=list)
    signals: dict[str, Any] = Field(default_factory=dict)
    reason: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolResult(BaseModel):
    """Result from a tool adapter invocation."""

    tool_name: str
    success: bool
    output: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RunEvent(BaseModel):
    """Single durable event in the run log."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    run_id: str
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentRunRequest(BaseModel):
    """Input to start an agent run."""

    question: str
    topic_hint: str | None = None
    provider: str | None = None
    model: str | None = None
    difficulty: str = "mid"


class AgentRunResult(BaseModel):
    """Final output of a completed agent run."""

    run_id: str
    state: RunState
    question: str
    topic: str
    provider: str
    model: str
    answer: str
    rationale_traces: list[DecisionRationale] = Field(default_factory=list)
    events: list[RunEvent] = Field(default_factory=list)
    error: str | None = None

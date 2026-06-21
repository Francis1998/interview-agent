"""Agent run orchestrator."""

from __future__ import annotations

from uuid import uuid4

import structlog

from interview_agent.config import Settings
from interview_agent.decision.engine import DecisionEngine
from interview_agent.lifecycle.event_log import EventLog
from interview_agent.lifecycle.state_machine import RunStateMachine
from interview_agent.llm.router import LLMRouter
from interview_agent.models import (
    AgentRunRequest,
    AgentRunResult,
    ChatMessage,
    EventType,
    RunState,
)
from interview_agent.safety.guard import RunCancelledError, SafetyGuard
from interview_agent.tools.registry import ToolRegistry

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """You are an expert technical interview coach.
Use the provided knowledge base context to answer interview questions.
Structure your answer with:
1. Direct answer (2-3 sentences)
2. Key trade-offs or comparisons
3. Concrete example
4. Common follow-up questions the interviewer might ask
Be concise, accurate, and interview-focused. Do not invent facts not supported by context."""


class AgentRunner:
    """Orchestrate a full agent run through the state machine."""

    def __init__(
        self,
        settings: Settings,
        event_log: EventLog,
        tool_registry: ToolRegistry,
        llm_router: LLMRouter,
    ) -> None:
        self._settings = settings
        self._event_log = event_log
        self._tools = tool_registry
        self._llm = llm_router
        self._sm = RunStateMachine()
        self._decisions = DecisionEngine(settings)
        self._safety = SafetyGuard(settings)

    async def _transition(
        self,
        run_id: str,
        current: RunState,
        target: RunState,
    ) -> RunState:
        self._safety.check_cancelled(run_id)
        self._sm.validate(current, target)
        await self._event_log.emit(
            run_id,
            EventType.STATE_TRANSITION,
            {"from": current.value, "to": target.value},
        )
        return target

    async def run(self, request: AgentRunRequest) -> AgentRunResult:
        """Execute a complete agent run."""
        run_id = str(uuid4())
        state = RunState.IDLE
        tool_calls = 0
        context = ""
        answer = ""
        provider = "mock"
        model = "mock-interview-v1"
        topic = ""

        self._decisions.reset()
        await self._event_log.emit(
            run_id,
            EventType.RUN_STARTED,
            {"question": request.question, "difficulty": request.difficulty},
        )

        try:

            async def _execute() -> AgentRunResult:
                nonlocal state, tool_calls, context, answer, provider, model, topic

                state = await self._transition(run_id, state, RunState.PLANNING)

                topic_trace = self._decisions.classify_topic(request)
                topic = topic_trace.chosen
                provider_trace = self._decisions.select_provider(request)
                provider = provider_trace.chosen
                model_trace = self._decisions.select_model(provider, request)
                model = model_trace.chosen

                for trace in self._decisions.traces:
                    await self._event_log.emit(
                        run_id,
                        EventType.DECISION,
                        trace.model_dump(mode="json"),
                    )

                self._safety.validate_question(request.question, topic)
                await self._event_log.emit(
                    run_id,
                    EventType.SAFETY_CHECK,
                    {"check": "scope", "passed": True, "topic": topic},
                )

                state = await self._transition(run_id, state, RunState.RETRIEVING)
                retrieval_trace = self._decisions.plan_retrieval(topic, request.question)
                await self._event_log.emit(
                    run_id,
                    EventType.DECISION,
                    retrieval_trace.model_dump(mode="json"),
                )

                kb_tool = self._tools.get("interview_kb_search")
                keywords = ",".join(str(k) for k in retrieval_trace.signals.get("keywords", []))
                if kb_tool:
                    self._safety.validate_tool_budget(tool_calls)
                    tool_calls += 1
                    await self._event_log.emit(
                        run_id,
                        EventType.TOOL_CALL,
                        {"tool": kb_tool.name, "topic": topic, "keywords": keywords},
                    )
                    result = await kb_tool.invoke(topic=topic, keywords=keywords)
                    context = result.output[: self._settings.max_context_chars]
                    await self._event_log.emit(
                        run_id,
                        EventType.TOOL_RESULT,
                        {"tool": kb_tool.name, "success": result.success, "chars": len(context)},
                    )

                state = await self._transition(run_id, state, RunState.REASONING)
                adapter = self._llm.get(provider)
                messages = [
                    ChatMessage(role="system", content=SYSTEM_PROMPT),
                    ChatMessage(
                        role="user",
                        content=(
                            f"Topic: {topic}\n"
                            f"Difficulty: {request.difficulty}\n\n"
                            f"Knowledge context:\n{context}\n\n"
                            f"Interview question:\n{request.question}"
                        ),
                    ),
                ]
                await self._event_log.emit(
                    run_id,
                    EventType.LLM_REQUEST,
                    {"provider": provider, "model": model},
                )
                llm_response = await adapter.complete(model, messages)
                answer = llm_response.content
                await self._event_log.emit(
                    run_id,
                    EventType.LLM_RESPONSE,
                    {
                        "provider": provider,
                        "model": model,
                        "latency_ms": llm_response.latency_ms,
                        "output_tokens": llm_response.output_tokens,
                    },
                )

                state = await self._transition(run_id, state, RunState.ANSWERING)
                state = await self._transition(run_id, state, RunState.DONE)
                await self._event_log.emit(
                    run_id,
                    EventType.RUN_COMPLETED,
                    {"state": state.value},
                )

                events = await self._event_log.get_events(run_id)
                return AgentRunResult(
                    run_id=run_id,
                    state=state,
                    question=request.question,
                    topic=topic,
                    provider=provider,
                    model=model,
                    answer=answer,
                    rationale_traces=self._decisions.traces,
                    events=events,
                )

            return await self._safety.with_timeout(_execute())

        except RunCancelledError as exc:
            await self._event_log.emit(run_id, EventType.RUN_CANCELLED, {"reason": str(exc)})
            return AgentRunResult(
                run_id=run_id,
                state=RunState.CANCELLED,
                question=request.question,
                topic=topic,
                provider=provider,
                model=model,
                answer="",
                rationale_traces=self._decisions.traces,
                events=await self._event_log.get_events(run_id),
                error=str(exc),
            )
        except Exception as exc:
            logger.exception("run_failed", run_id=run_id)
            await self._event_log.emit(run_id, EventType.RUN_FAILED, {"error": str(exc)})
            return AgentRunResult(
                run_id=run_id,
                state=RunState.ERROR,
                question=request.question,
                topic=topic,
                provider=provider,
                model=model,
                answer=answer,
                rationale_traces=self._decisions.traces,
                events=await self._event_log.get_events(run_id),
                error=str(exc),
            )

    def cancel(self, run_id: str) -> None:
        """Request cancellation of an in-flight run."""
        self._safety.cancel_run(run_id)

"""Mock LLM adapter for offline tests and demos."""

from __future__ import annotations

import time

from interview_agent.llm.base import BaseLLMAdapter
from interview_agent.models import ChatMessage, LLMResponse


class MockAdapter(BaseLLMAdapter):
    """Deterministic mock responses without external API calls."""

    provider_name = "mock"

    async def complete(
        self,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 2048,
    ) -> LLMResponse:
        start = time.perf_counter()
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        answer = (
            "## Interview Answer (Mock Mode)\n\n"
            f"**Question context:** {user_msg[:200]}...\n\n"
            "1. **Definition** — State the core concept clearly.\n"
            "2. **Trade-offs** — Compare alternatives and when to use each.\n"
            "3. **Example** — Give a concrete scenario from production.\n"
            "4. **Follow-up** — Mention what you'd probe deeper in a live interview.\n\n"
            "_Configure OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or KIMI_API_KEY "
            "for live LLM responses._"
        )
        return LLMResponse(
            provider=self.provider_name,
            model=model,
            content=answer,
            input_tokens=len(user_msg.split()),
            output_tokens=len(answer.split()),
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    async def health_check(self) -> bool:
        return True

"""OpenAI (GPT) adapter."""

from __future__ import annotations

import time

from openai import AsyncOpenAI

from interview_agent.llm.base import BaseLLMAdapter, ProviderError
from interview_agent.models import ChatMessage, LLMResponse


class OpenAIAdapter(BaseLLMAdapter):
    """GPT models via OpenAI API."""

    provider_name = "openai"

    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)

    async def complete(
        self,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 2048,
    ) -> LLMResponse:
        start = time.perf_counter()
        try:
            payload = [{"role": m.role, "content": m.content} for m in messages]
            response = await self._client.chat.completions.create(
                model=model,
                messages=payload,  # type: ignore[arg-type]
                max_tokens=max_tokens,
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI request failed: {exc}") from exc
        choice = response.choices[0].message
        usage = response.usage
        return LLMResponse(
            provider=self.provider_name,
            model=model,
            content=choice.content or "",
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    async def health_check(self) -> bool:
        return bool(self._client.api_key)

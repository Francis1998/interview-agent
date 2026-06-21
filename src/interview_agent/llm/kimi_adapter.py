"""Kimi (Moonshot AI) adapter — OpenAI-compatible API."""

from __future__ import annotations

import time

from openai import AsyncOpenAI

from interview_agent.llm.base import BaseLLMAdapter, ProviderError
from interview_agent.models import ChatMessage, LLMResponse

KIMI_BASE_URL = "https://api.moonshot.cn/v1"


class KimiAdapter(BaseLLMAdapter):
    """Kimi models via Moonshot OpenAI-compatible endpoint."""

    provider_name = "kimi"

    def __init__(self, api_key: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=KIMI_BASE_URL)

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
            raise ProviderError(f"Kimi request failed: {exc}") from exc
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

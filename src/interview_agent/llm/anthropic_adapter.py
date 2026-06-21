"""Anthropic (Claude) adapter."""

from __future__ import annotations

import time

import anthropic

from interview_agent.llm.base import BaseLLMAdapter, ProviderError
from interview_agent.models import ChatMessage, LLMResponse


class AnthropicAdapter(BaseLLMAdapter):
    """Claude models via Anthropic API."""

    provider_name = "anthropic"

    def __init__(self, api_key: str) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(
        self,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 2048,
    ) -> LLMResponse:
        start = time.perf_counter()
        system = ""
        chat_messages: list[dict[str, str]] = []
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})
        try:
            if system:
                response = await self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=chat_messages,  # type: ignore[arg-type]
                )
            else:
                response = await self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=chat_messages,  # type: ignore[arg-type]
                )
        except Exception as exc:
            raise ProviderError(f"Anthropic request failed: {exc}") from exc
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResponse(
            provider=self.provider_name,
            model=model,
            content=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    async def health_check(self) -> bool:
        return bool(self._client.api_key)

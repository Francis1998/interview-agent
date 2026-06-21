"""Google Gemini adapter."""

from __future__ import annotations

import time

import google.generativeai as genai

from interview_agent.llm.base import BaseLLMAdapter, ProviderError
from interview_agent.models import ChatMessage, LLMResponse


class GeminiAdapter(BaseLLMAdapter):
    """Gemini models via Google Generative AI API."""

    provider_name = "google"

    def __init__(self, api_key: str) -> None:
        genai.configure(api_key=api_key)  # type: ignore[attr-defined]
        self._configured = bool(api_key)

    async def complete(
        self,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 2048,
    ) -> LLMResponse:
        start = time.perf_counter()
        prompt_parts: list[str] = []
        for msg in messages:
            prefix = msg.role.upper()
            prompt_parts.append(f"[{prefix}]\n{msg.content}")
        prompt = "\n\n".join(prompt_parts)
        try:
            gemini_model = genai.GenerativeModel(model)  # type: ignore[attr-defined]
            response = await gemini_model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(max_output_tokens=max_tokens),  # type: ignore[attr-defined]
            )
        except Exception as exc:
            raise ProviderError(f"Gemini request failed: {exc}") from exc
        text = response.text or ""
        return LLMResponse(
            provider=self.provider_name,
            model=model,
            content=text,
            input_tokens=0,
            output_tokens=0,
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    async def health_check(self) -> bool:
        return self._configured

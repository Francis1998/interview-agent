"""LLM provider registry and router."""

from __future__ import annotations

from interview_agent.config import Settings
from interview_agent.llm.anthropic_adapter import AnthropicAdapter
from interview_agent.llm.base import BaseLLMAdapter
from interview_agent.llm.gemini_adapter import GeminiAdapter
from interview_agent.llm.kimi_adapter import KimiAdapter
from interview_agent.llm.mock_adapter import MockAdapter
from interview_agent.llm.openai_adapter import OpenAIAdapter


class LLMRouter:
    """Resolve provider name to adapter instance."""

    def __init__(self, settings: Settings) -> None:
        self._adapters: dict[str, BaseLLMAdapter] = {}
        if settings.openai_api_key:
            self._adapters["openai"] = OpenAIAdapter(settings.openai_api_key)
        if settings.anthropic_api_key:
            self._adapters["anthropic"] = AnthropicAdapter(settings.anthropic_api_key)
        if settings.google_api_key:
            self._adapters["google"] = GeminiAdapter(settings.google_api_key)
        if settings.kimi_api_key:
            self._adapters["kimi"] = KimiAdapter(settings.kimi_api_key)
        self._adapters["mock"] = MockAdapter()

    def get(self, provider: str) -> BaseLLMAdapter:
        """Return adapter for provider or mock fallback."""
        return self._adapters.get(provider, self._adapters["mock"])

    def available_providers(self) -> list[str]:
        """List providers with configured adapters."""
        return [name for name, adapter in self._adapters.items() if name != "mock"]

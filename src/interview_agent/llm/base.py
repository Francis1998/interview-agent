"""Base LLM adapter interface."""

from abc import ABC, abstractmethod

from interview_agent.models import ChatMessage, LLMResponse


class ProviderError(RuntimeError):
    """Raised when a provider request fails."""


class BaseLLMAdapter(ABC):
    """Provider adapter contract."""

    provider_name: str

    @abstractmethod
    async def complete(
        self,
        model: str,
        messages: list[ChatMessage],
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Return a normalized completion."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check provider availability."""

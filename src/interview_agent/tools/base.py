"""Base tool adapter interface."""

from abc import ABC, abstractmethod

from interview_agent.models import ToolResult


class BaseTool(ABC):
    """Contract for external integrations invoked by the agent."""

    name: str
    description: str

    @abstractmethod
    async def invoke(self, **kwargs: str) -> ToolResult:
        """Execute the tool with keyword arguments."""

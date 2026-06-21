"""Interview knowledge base search tool."""

from __future__ import annotations

import re
from pathlib import Path

from interview_agent.models import ToolResult
from interview_agent.tools.base import BaseTool


class InterviewKBTool(BaseTool):
    """Search bundled markdown interview guides by topic and keywords."""

    name = "interview_kb_search"
    description = "Search interview knowledge base markdown files for relevant sections."

    def __init__(self, knowledge_dir: Path, max_chars: int = 4000) -> None:
        self._knowledge_dir = knowledge_dir
        self._max_chars = max_chars

    async def invoke(self, **kwargs: str) -> ToolResult:
        topic = kwargs.get("topic", "")
        keywords_raw = kwargs.get("keywords", "")
        keywords = [k.strip().lower() for k in keywords_raw.split(",") if k.strip()]

        path = self._knowledge_dir / f"{topic}.md"
        if not path.exists():
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=f"Topic file not found: {topic}.md",
                metadata={"topic": topic},
            )

        content = path.read_text(encoding="utf-8")
        if not keywords:
            snippet = content[: self._max_chars]
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=snippet,
                metadata={"topic": topic, "method": "head"},
            )

        sections = re.split(r"\n(?=#{1,3} )", content)
        scored: list[tuple[int, str]] = []
        for section in sections:
            lower = section.lower()
            score = sum(lower.count(kw) for kw in keywords)
            if score > 0:
                scored.append((score, section))

        scored.sort(key=lambda x: x[0], reverse=True)
        combined = ""
        for _, section in scored[:5]:
            if len(combined) + len(section) > self._max_chars:
                break
            combined += section + "\n\n"

        if not combined:
            combined = content[: self._max_chars]

        return ToolResult(
            tool_name=self.name,
            success=True,
            output=combined.strip(),
            metadata={"topic": topic, "keywords": keywords, "sections_matched": len(scored)},
        )

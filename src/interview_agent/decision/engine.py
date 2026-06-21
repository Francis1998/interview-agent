"""Deterministic decision engine with rationale traces."""

from __future__ import annotations

import re
from typing import Any

from interview_agent.config import Settings
from interview_agent.models import AgentRunRequest, DecisionRationale

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "python": ["python", "gil", "decorator", "async", "django", "flask", "fastapi"],
    "golang": ["go ", "golang", "goroutine", "channel", "gcp", "select", "gc "],
    "mysql": ["mysql", "sql", "index", "b+ tree", "b-tree", "innodb", "transaction", "acid"],
    "linux": ["linux", "epoll", "shell", "process", "top ", "signal", "kernel"],
    "networking": ["tcp", "udp", "http", "dns", "tls", "ssl", "websocket", "network"],
    "operating-systems": ["os ", "thread", "mutex", "ipc", "kernel", "user mode", "process"],
    "redis": ["redis", "cache", "lru", "eviction", "pub/sub"],
    "algorithms": ["algorithm", "sort", "heap", "top-k", "complexity", "big-o", "red-black"],
    "system-design": ["system design", "scalability", "load balanc", "cap ", "sharding", "cdn"],
}

PROVIDER_PRIORITY = ["openai", "anthropic", "google", "kimi"]


class DecisionEngine:
    """Rule-based engine that selects topic, provider, and strategy deterministically."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._traces: list[DecisionRationale] = []

    @property
    def traces(self) -> list[DecisionRationale]:
        """Return accumulated rationale traces for the current run."""
        return list(self._traces)

    def reset(self) -> None:
        """Clear traces for a new run."""
        self._traces.clear()

    def _record(
        self,
        step: str,
        chosen: str,
        alternatives: list[str],
        signals: dict[str, Any],
        reason: str,
    ) -> DecisionRationale:
        trace = DecisionRationale(
            step=step,
            chosen=chosen,
            alternatives=alternatives,
            signals=signals,
            reason=reason,
        )
        self._traces.append(trace)
        return trace

    def classify_topic(self, request: AgentRunRequest) -> DecisionRationale:
        """Deterministically classify question into an interview topic."""
        allowlist = self._settings.topic_allowlist
        text = request.question.lower()

        if request.topic_hint and request.topic_hint.lower() in allowlist:
            return self._record(
                step="topic_classification",
                chosen=request.topic_hint.lower(),
                alternatives=sorted(allowlist),
                signals={"hint": request.topic_hint, "method": "explicit_hint"},
                reason="User provided an explicit topic hint within allowlist.",
            )

        scores: dict[str, int] = {}
        for topic, keywords in TOPIC_KEYWORDS.items():
            if topic not in allowlist:
                continue
            score = sum(1 for kw in keywords if kw in text)
            if score:
                scores[topic] = score

        if scores:
            chosen = max(scores, key=lambda k: scores[k])
            return self._record(
                step="topic_classification",
                chosen=chosen,
                alternatives=sorted(allowlist - {chosen}),
                signals={"scores": scores, "method": "keyword_scoring"},
                reason=f"Highest keyword score ({scores[chosen]}) for topic '{chosen}'.",
            )

        fallback = "system-design" if "system-design" in allowlist else sorted(allowlist)[0]
        return self._record(
            step="topic_classification",
            chosen=fallback,
            alternatives=sorted(allowlist - {fallback}),
            signals={"scores": scores, "method": "fallback"},
            reason="No keyword match; defaulting to general system-design guidance.",
        )

    def select_provider(self, request: AgentRunRequest) -> DecisionRationale:
        """Select LLM provider based on availability and request override."""
        available: list[str] = []
        key_map = {
            "openai": self._settings.openai_api_key,
            "anthropic": self._settings.anthropic_api_key,
            "google": self._settings.google_api_key,
            "kimi": self._settings.kimi_api_key,
        }
        for name, key in key_map.items():
            if key:
                available.append(name)

        if request.provider and request.provider in available:
            return self._record(
                step="provider_selection",
                chosen=request.provider,
                alternatives=[p for p in available if p != request.provider],
                signals={"available": available, "override": True},
                reason="User requested provider with valid API key.",
            )

        default = self._settings.default_provider
        if default in available:
            return self._record(
                step="provider_selection",
                chosen=default,
                alternatives=[p for p in available if p != default],
                signals={"available": available, "override": False},
                reason=f"Using configured default provider '{default}'.",
            )

        for name in PROVIDER_PRIORITY:
            if name in available:
                return self._record(
                    step="provider_selection",
                    chosen=name,
                    alternatives=[p for p in available if p != name],
                    signals={"available": available, "override": False},
                    reason=f"Fallback to first available provider '{name}'.",
                )

        return self._record(
            step="provider_selection",
            chosen="mock",
            alternatives=[],
            signals={"available": available},
            reason="No API keys configured; using mock provider for offline demo.",
        )

    def select_model(self, provider: str, request: AgentRunRequest) -> DecisionRationale:
        """Select model for the chosen provider."""
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-latest",
            "google": "gemini-1.5-flash",
            "kimi": "moonshot-v1-8k",
            "mock": "mock-interview-v1",
        }
        if request.model:
            return self._record(
                step="model_selection",
                chosen=request.model,
                alternatives=[defaults.get(provider, "unknown")],
                signals={"provider": provider, "override": True},
                reason="User requested specific model.",
            )
        if request.model is None and self._settings.default_model and provider == "openai":
            chosen = self._settings.default_model
        else:
            chosen = defaults.get(provider, "gpt-4o-mini")
        return self._record(
            step="model_selection",
            chosen=chosen,
            alternatives=[v for k, v in defaults.items() if k != provider],
            signals={"provider": provider, "difficulty": request.difficulty},
            reason=f"Default model for provider '{provider}' at difficulty '{request.difficulty}'.",
        )

    def plan_retrieval(self, topic: str, question: str) -> DecisionRationale:
        """Decide retrieval strategy."""
        keywords = re.findall(r"[a-zA-Z]{3,}", question.lower())[:8]
        return self._record(
            step="retrieval_plan",
            chosen="keyword_search",
            alternatives=["full_file", "semantic_search"],
            signals={"topic": topic, "keywords": keywords},
            reason="Keyword search over topic markdown is deterministic and bounded.",
        )

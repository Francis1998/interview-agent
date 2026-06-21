# Architecture

## Overview

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  CLI / API  │────▶│   AgentRunner    │────▶│  LLM Adapters   │
└─────────────┘     │  (orchestrator)  │     │ GPT/Claude/     │
                    └────────┬─────────┘     │ Gemini/Kimi     │
                             │               └─────────────────┘
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ Decision   │  │ State      │  │ Tool       │
     │ Engine     │  │ Machine    │  │ Registry   │
     └────────────┘  └────────────┘  └─────┬──────┘
              │              │              │
              ▼              ▼              ▼
     ┌────────────┐  ┌────────────┐  ┌────────────┐
     │ Rationale  │  │ Event Log  │  │ Interview  │
     │ Traces     │  │ (JSONL)    │  │ KB Tool    │
     └────────────┘  └────────────┘  └────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
             ┌────────────┐    ┌────────────┐
             │ Safety     │    │ Alembic    │
             │ Guard      │    │ Migrations │
             └────────────┘    └────────────┘
```

## Run Lifecycle (State Machine)

```
IDLE → PLANNING → RETRIEVING → REASONING → ANSWERING → DONE
  │        │           │            │           │
  └────────┴───────────┴────────────┴───────────┴──▶ ERROR
  └────────┴───────────┴────────────┴───────────┴──▶ CANCELLED
```

Transitions are validated by `RunStateMachine` — invalid jumps raise `InvalidTransitionError`.

## Decision Engine

Rule-based, **deterministic** engine (not LLM-driven planning):

1. **Topic classification** — keyword scoring over question text, or explicit hint.
2. **Provider selection** — user override → configured default → first available key.
3. **Model selection** — provider-specific defaults or user override.
4. **Retrieval plan** — keyword extraction for KB search.

Each step emits a `DecisionRationale` with `chosen`, `alternatives`, `signals`, and `reason`.

## LLM Adapter Layer

All providers implement `BaseLLMAdapter`:

```python
async def complete(model, messages, max_tokens) -> LLMResponse
async def health_check() -> bool
```

| Adapter | Provider | API |
|---------|----------|-----|
| `OpenAIAdapter` | openai | OpenAI Chat Completions |
| `AnthropicAdapter` | anthropic | Anthropic Messages API |
| `GeminiAdapter` | google | Google Generative AI |
| `KimiAdapter` | kimi | Moonshot OpenAI-compatible |
| `MockAdapter` | mock | Offline deterministic responses |

`LLMRouter` resolves provider name → adapter instance.

## Tool Adapters

Tools implement `BaseTool.invoke(**kwargs) -> ToolResult`.

Current tools:
- **`interview_kb_search`** — reads `knowledge/*.md`, keyword-scores sections, returns bounded context.

Designed for extension: add tools by registering in `ToolRegistry`.

## Event Log

Append-only JSONL per run at `{EVENT_LOG_DIR}/{run_id}.jsonl`.

Enables:
- Post-run debugging
- Audit compliance
- Replay/analysis of decision traces

## Package Layout

```
src/interview_agent/
├── agent/runner.py       # Orchestrator
├── decision/engine.py    # Deterministic decisions
├── lifecycle/
│   ├── state_machine.py
│   └── event_log.py
├── llm/                  # Provider adapters
├── tools/                # External integrations
├── safety/guard.py       # Scope, timeout, cancel
├── api/main.py           # FastAPI demo
└── cli.py                # Typer CLI
```

## Data Flow (Single Run)

1. Client sends `AgentRunRequest` (question, optional topic/provider).
2. Runner transitions to `PLANNING`; decision engine classifies topic and selects provider/model.
3. Safety guard validates scope.
4. Runner transitions to `RETRIEVING`; KB tool searches topic markdown.
5. Runner transitions to `REASONING`; LLM adapter generates answer from context + question.
6. Runner transitions to `ANSWERING` → `DONE`; returns `AgentRunResult` with answer, traces, events.

## Future Extensions

- SQL persistence for runs (Alembic scaffold ready)
- Semantic retrieval (embeddings) alongside keyword search
- Streaming LLM responses via SSE
- Multi-turn mock interview sessions

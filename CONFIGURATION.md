# Configuration

All settings are loaded from environment variables or a `.env` file in the project root.

## LLM Providers

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
KIMI_API_KEY=...
```

Kimi uses the Moonshot OpenAI-compatible endpoint (`https://api.moonshot.cn/v1`).

### Defaults

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_LLM_PROVIDER` | `openai` | Provider when none specified |
| `DEFAULT_LLM_MODEL` | `gpt-4o-mini` | Model for OpenAI provider |

The decision engine auto-selects the first provider with a configured API key if the default is unavailable.

## Safety Bounds

| Variable | Default | Description |
|----------|---------|-------------|
| `RUN_TIMEOUT_SECONDS` | `120` | Max wall-clock time per agent run |
| `MAX_TOOL_CALLS` | `5` | Max tool invocations per run |
| `MAX_CONTEXT_CHARS` | `12000` | Max KB context passed to LLM |
| `ALLOWED_TOPICS` | comma-separated list | Topic scope allowlist |

## Storage

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/interview_agent.db` | SQLAlchemy URL for migrations |
| `EVENT_LOG_DIR` | `./data/events` | JSONL durable event logs per run |
| `KNOWLEDGE_DIR` | `./knowledge` | Interview markdown knowledge base |

## Server

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `127.0.0.1` | Demo server bind address |
| `PORT` | `8080` | Demo server port |

## Migrations

Alembic scaffold is included for future run-metadata persistence:

```bash
alembic upgrade head
```

Currently, event logs are file-backed JSONL; the DB migration scaffold is ready for SQL persistence.

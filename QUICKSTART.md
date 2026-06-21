# Quickstart

Get **Interview Agent** running in under 5 minutes.

## Prerequisites

- Python 3.10+
- At least one LLM API key (optional — mock mode works offline)

## Install

```bash
git clone https://github.com/Francis1998/interview-agent.git
cd interview-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your API keys
```

## CLI — Ask a Question

```bash
interview-agent ask "Explain the Python GIL and when multithreading still helps"
```

With options:

```bash
interview-agent ask "How does Go GC work?" --topic golang --provider openai --difficulty senior
```

## Web Demo Server

```bash
interview-agent serve --port 8080
# Open http://127.0.0.1:8080
```

## Inspect Event Log

After a run, copy the `run_id` from CLI output:

```bash
interview-agent events <run-id>
```

## Generate Demo GIF

```bash
make demo-gif
# Output: assets/demo-agent-run.gif
```

## Run Tests

```bash
make validate
```

## Supported LLM Providers

| Provider | Env Variable | Default Model |
|----------|--------------|---------------|
| OpenAI (GPT) | `OPENAI_API_KEY` | gpt-4o-mini |
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | claude-3-5-haiku-latest |
| Google (Gemini) | `GOOGLE_API_KEY` | gemini-1.5-flash |
| Kimi (Moonshot) | `KIMI_API_KEY` | moonshot-v1-8k |
| Mock (offline) | — | mock-interview-v1 |

Without API keys, the agent runs in **mock mode** — useful for CI and local development.

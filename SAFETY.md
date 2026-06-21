# Safety

Interview Agent is designed for **bounded, auditable** interview coaching — not open-ended autonomous action.

## Controls Implemented

### 1. Bounded Scope

- Questions limited to **2000 characters**.
- Topics restricted to an explicit **allowlist** (`ALLOWED_TOPICS`).
- Out-of-scope topics raise `ScopeViolationError` before any LLM call.

### 2. Timeouts

- Every agent run wrapped in `asyncio.wait_for` with `RUN_TIMEOUT_SECONDS` (default 120s).
- Prevents hung runs from blocking workers indefinitely.

### 3. Tool Call Budget

- Max `MAX_TOOL_CALLS` (default 5) KB retrievals per run.
- Prevents runaway tool loops.

### 4. Cancellation

- `POST /api/cancel/{run_id}` or `runner.cancel(run_id)` sets a cancellation flag.
- Checked at each state transition; raises `RunCancelledError`.

### 5. Context Truncation

- KB retrieval output truncated to `MAX_CONTEXT_CHARS` before LLM prompt.
- Reduces token cost and prompt injection surface from oversized context.

## Audit Trail

Every run produces a **durable JSONL event log**:

| Event | When |
|-------|------|
| `run_started` | Run begins |
| `state_transition` | Each state machine transition |
| `decision` | Each deterministic decision with rationale |
| `tool_call` / `tool_result` | KB retrieval |
| `llm_request` / `llm_response` | LLM invocation metadata |
| `safety_check` | Scope validation |
| `run_completed` / `run_failed` / `run_cancelled` | Terminal states |

Inspect via CLI: `interview-agent events <run-id>`

## LLM Output Handling

- LLM responses are **consumed and returned** to the caller — not executed.
- No code execution, shell commands, or arbitrary tool side effects beyond KB read.
- Mock provider available for offline/CI without external API calls.

## Recommendations for Production

1. Run behind authentication (not included in demo server).
2. Rate-limit `/api/run` per user/IP.
3. Log provider + token usage for cost monitoring.
4. Rotate API keys via secrets manager, not committed `.env`.
5. Review `ALLOWED_TOPICS` for your deployment context.

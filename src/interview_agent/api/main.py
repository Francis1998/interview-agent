"""FastAPI demo server."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from interview_agent.agent.runner import AgentRunner
from interview_agent.config import Settings, get_settings
from interview_agent.lifecycle.event_log import EventLog
from interview_agent.llm.router import LLMRouter
from interview_agent.models import AgentRunRequest, AgentRunResult
from interview_agent.tools.interview_kb import InterviewKBTool
from interview_agent.tools.registry import ToolRegistry

DEMO_DIR = Path(__file__).resolve().parents[3] / "demo"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build FastAPI application with dependency wiring."""
    cfg = settings or get_settings()
    cfg.event_log_dir.mkdir(parents=True, exist_ok=True)
    cfg.knowledge_dir.mkdir(parents=True, exist_ok=True)

    event_log = EventLog(cfg.event_log_dir)
    tools = ToolRegistry()
    tools.register(InterviewKBTool(cfg.knowledge_dir, max_chars=cfg.max_context_chars))
    llm_router = LLMRouter(cfg)
    runner = AgentRunner(cfg, event_log, tools, llm_router)

    app = FastAPI(
        title="Interview Agent",
        description="AI interview coach with deterministic decisions and rationale traces",
        version="0.1.0",
    )

    static_dir = DEMO_DIR / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> FileResponse:
        return FileResponse(DEMO_DIR / "index.html")

    @app.get("/health")
    async def health() -> dict[str, str | list[str]]:
        return {
            "status": "ok",
            "providers": llm_router.available_providers() or ["mock"],
        }

    @app.post("/api/run", response_model=AgentRunResult)
    async def run_agent(request: AgentRunRequest) -> AgentRunResult:
        return await runner.run(request)

    @app.get("/api/events/{run_id}")
    async def get_events(run_id: str) -> list[dict[str, Any]]:
        events = await event_log.get_events(run_id)
        return [e.model_dump(mode="json") for e in events]

    @app.post("/api/cancel/{run_id}")
    async def cancel_run(run_id: str) -> dict[str, str]:
        runner.cancel(run_id)
        return {"status": "cancelled", "run_id": run_id}

    class ProviderStatus(BaseModel):
        name: str
        available: bool

    @app.get("/api/providers")
    async def list_providers() -> list[ProviderStatus]:
        statuses = []
        for name in ["openai", "anthropic", "google", "kimi", "mock"]:
            adapter = llm_router.get(name)
            ok = await adapter.health_check()
            statuses.append(ProviderStatus(name=name, available=ok))
        return statuses

    return app


app = create_app()

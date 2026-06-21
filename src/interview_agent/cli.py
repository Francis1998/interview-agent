"""CLI entry point."""

from __future__ import annotations

import asyncio
import json

import typer
import uvicorn
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from interview_agent.agent.runner import AgentRunner
from interview_agent.config import get_settings
from interview_agent.lifecycle.event_log import EventLog
from interview_agent.llm.router import LLMRouter
from interview_agent.models import AgentRunRequest
from interview_agent.tools.interview_kb import InterviewKBTool
from interview_agent.tools.registry import ToolRegistry

app = typer.Typer(name="interview-agent", help="AI interview coach CLI")
console = Console()


def _build_runner() -> AgentRunner:
    settings = get_settings()
    settings.event_log_dir.mkdir(parents=True, exist_ok=True)
    event_log = EventLog(settings.event_log_dir)
    tools = ToolRegistry()
    tools.register(InterviewKBTool(settings.knowledge_dir))
    llm_router = LLMRouter(settings)
    return AgentRunner(settings, event_log, tools, llm_router)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Interview question to answer"),
    topic: str | None = typer.Option(None, "--topic", "-t", help="Topic hint"),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    difficulty: str = typer.Option("mid", "--difficulty", "-d"),
) -> None:
    """Ask an interview question and print the agent response."""

    async def _run() -> None:
        runner = _build_runner()
        result = await runner.run(
            AgentRunRequest(
                question=question,
                topic_hint=topic,
                provider=provider,
                difficulty=difficulty,
            )
        )
        console.print(Panel(Markdown(result.answer or result.error or "No answer"), title="Answer"))
        table = Table(title="Decision Rationale Traces")
        table.add_column("Step")
        table.add_column("Chosen")
        table.add_column("Reason")
        for trace in result.rationale_traces:
            table.add_row(trace.step, trace.chosen, trace.reason[:80])
        console.print(table)
        console.print(f"[dim]run_id={result.run_id} state={result.state.value}[/dim]")

    asyncio.run(_run())


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8080, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Start the demo web server."""
    uvicorn.run(
        "interview_agent.api.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def events(run_id: str = typer.Argument(..., help="Run ID to inspect")) -> None:
    """Print durable event log for a run."""

    async def _show() -> None:
        settings = get_settings()
        log = EventLog(settings.event_log_dir)
        for event in await log.get_events(run_id):
            console.print_json(json.dumps(event.model_dump(mode="json"), default=str))

    asyncio.run(_show())


if __name__ == "__main__":
    app()

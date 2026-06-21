"""Application configuration via environment variables."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM provider keys
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    kimi_api_key: str = Field(default="", alias="KIMI_API_KEY")

    # Defaults
    default_provider: str = Field(default="openai", alias="DEFAULT_LLM_PROVIDER")
    default_model: str = Field(default="gpt-4o-mini", alias="DEFAULT_LLM_MODEL")

    # Safety
    run_timeout_seconds: float = Field(default=120.0, alias="RUN_TIMEOUT_SECONDS")
    max_tool_calls: int = Field(default=5, alias="MAX_TOOL_CALLS")
    max_context_chars: int = Field(default=12000, alias="MAX_CONTEXT_CHARS")
    allowed_topics: str = Field(
        default="python,golang,mysql,linux,networking,operating-systems,redis,algorithms,system-design",
        alias="ALLOWED_TOPICS",
    )

    # Storage
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/interview_agent.db",
        alias="DATABASE_URL",
    )
    event_log_dir: Path = Field(default=Path("./data/events"), alias="EVENT_LOG_DIR")
    knowledge_dir: Path = Field(default=Path("./knowledge"), alias="KNOWLEDGE_DIR")

    # Server
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8080, alias="PORT")

    @property
    def topic_allowlist(self) -> set[str]:
        """Return parsed topic allowlist."""
        return {t.strip().lower() for t in self.allowed_topics.split(",") if t.strip()}


def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()

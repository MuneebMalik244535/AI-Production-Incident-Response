"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration — every value can be overridden via env vars or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── LLM Providers ──────────────────────────────────────────────────────────
    openai_api_key: str = ""

    # ── GitHub Integration ─────────────────────────────────────────────────────
    github_token: str = ""
    github_default_repo: str = ""

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/incidents"

    # ── Supabase (optional) ────────────────────────────────────────────────────
    supabase_url: str = ""
    supabase_key: str = ""

    # ── Slack ──────────────────────────────────────────────────────────────────
    slack_webhook_url: str = ""

    # ── Application ────────────────────────────────────────────────────────────
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"


# Singleton — import this everywhere
settings = Settings()

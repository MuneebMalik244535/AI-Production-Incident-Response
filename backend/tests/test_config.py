"""Tests for application configuration."""

from __future__ import annotations

from app.config import Settings, settings


class TestSettings:
    """Configuration should load defaults correctly."""

    def test_singleton_exists(self) -> None:
        assert settings is not None

    def test_default_app_env(self) -> None:
        s = Settings()
        assert s.app_env == "development"

    def test_default_port(self) -> None:
        s = Settings()
        assert s.app_port == 8000

    def test_default_debug(self) -> None:
        s = Settings()
        assert s.app_debug is True

    def test_default_log_level(self) -> None:
        s = Settings()
        assert s.log_level == "INFO"

    def test_database_url_has_default(self) -> None:
        s = Settings()
        assert "postgresql" in s.database_url
        assert "asyncpg" in s.database_url

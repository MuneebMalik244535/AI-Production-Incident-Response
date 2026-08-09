"""Pydantic schemas for MCP server tool parameters and return types."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


# ── Log Server Schemas ────────────────────────────────────────────────────────


class LogEntry(BaseModel):
    """A single log entry."""

    id: str
    service: str
    severity: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)
    stack_trace: str | None = None


class ErrorSummary(BaseModel):
    """Aggregated error stats for a service."""

    service: str
    time_range_minutes: int
    total_errors: int
    error_counts_by_severity: dict[str, int]
    top_error_messages: list[dict[str, Any]]
    spike_detected: bool = False
    increase_percentage: float = 0.0


# ── GitHub Server Schemas ─────────────────────────────────────────────────────


class CommitSummary(BaseModel):
    """Summary of a GitHub commit."""

    sha: str
    message: str
    author: str
    date: datetime
    url: str
    files_changed_count: int = 0


class CommitDetail(BaseModel):
    """Full detail of a GitHub commit including file diffs."""

    sha: str
    message: str
    author: str
    date: datetime
    url: str
    stats: dict[str, int] = Field(default_factory=dict)  # additions, deletions, total
    files: list[dict[str, Any]] = Field(default_factory=list)


class CodeMatch(BaseModel):
    """Match result from code search."""

    path: str
    repo: str
    line_number: int | None = None
    code_snippet: str
    html_url: str


class PullRequestDetail(BaseModel):
    """Detail of a GitHub Pull Request."""

    number: int
    title: str
    state: str
    author: str
    created_at: datetime
    merged_at: datetime | None = None
    body: str = ""
    html_url: str
    diff_url: str = ""

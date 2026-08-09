"""Pydantic models for agent structured outputs."""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

from app.schemas.incident import Severity


class LogFindings(BaseModel):
    """Structured output from the Log Analysis Agent."""

    service: str
    error_count: int
    error_patterns: list[str] = Field(default_factory=list)
    affected_endpoints: list[str] = Field(default_factory=list)
    time_correlation: str = ""
    severity_assessment: Severity = Severity.HIGH
    raw_evidence: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""


class GitHubFindings(BaseModel):
    """Structured output from the GitHub Investigation Agent."""

    repository: str
    suspicious_commits: list[dict[str, Any]] = Field(default_factory=list)
    relevant_files: list[str] = Field(default_factory=list)
    code_changes_summary: str = ""
    deployment_correlation: str = ""
    summary: str = ""


class RootCauseAnalysis(BaseModel):
    """Structured output from the Root Cause Agent."""

    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    contributing_factors: list[str] = Field(default_factory=list)
    timeline_summary: str = ""
    suspected_commit: str | None = None


class IncidentRecommendation(BaseModel):
    """Structured output from the Recommendation Agent."""

    root_cause: str
    evidence: list[str] = Field(default_factory=list)
    risk_level: Severity
    recommended_actions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_pr_title: str = ""
    suggested_pr_description: str = ""
    requires_immediate_action: bool = False

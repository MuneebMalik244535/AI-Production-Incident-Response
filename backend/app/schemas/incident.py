"""Pydantic schemas for incidents, agent findings, and recommendations."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────


class Severity(str, Enum):
    """Incident severity levels."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    """Lifecycle status of an incident."""

    RECEIVED = "RECEIVED"
    INVESTIGATING = "INVESTIGATING"
    ANALYZED = "ANALYZED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RESOLVED = "RESOLVED"


class ApprovalDecision(str, Enum):
    """Human approval decisions."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"


# ── Request Schemas ────────────────────────────────────────────────────────────


class IncidentCreate(BaseModel):
    """Payload to create a new incident and trigger investigation."""

    error: str = Field(..., description="Error message or description", examples=["Database connection timeout"])
    service: str = Field(..., description="Affected service name", examples=["payment-api"])
    severity: Severity = Field(..., description="Incident severity level")
    timestamp: datetime | None = Field(
        default=None,
        description="When the error first occurred (defaults to now)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (e.g., region, user_id, request_id)",
    )


class ApprovalRequest(BaseModel):
    """Payload for human approval/rejection of a recommendation."""

    decision: ApprovalDecision
    reviewer: str = Field(..., description="Name or email of the reviewer")
    notes: str = Field(default="", description="Optional reviewer notes")
    action: str = Field(
        default="",
        description="Action to take on approval (e.g., 'create_pr', 'notify_slack')",
    )


# ── Agent Finding Schemas ──────────────────────────────────────────────────────


class AgentFinding(BaseModel):
    """A single finding produced by an agent during investigation."""

    agent_name: str
    finding_type: str = Field(..., description="Type: log_analysis, github, root_cause, etc.")
    content: str = Field(..., description="Human-readable finding summary")
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score 0-1")


class Recommendation(BaseModel):
    """Final recommendation produced by the Recommendation Agent."""

    root_cause: str
    evidence: list[str]
    risk_level: Severity
    recommended_actions: list[str]
    confidence: float = Field(ge=0.0, le=1.0)
    suggested_pr_description: str = ""
    requires_immediate_action: bool = False


# ── Response Schemas ───────────────────────────────────────────────────────────


class AgentRunResponse(BaseModel):
    """Summary of a single agent's execution."""

    agent_name: str
    status: str
    duration_seconds: float | None = None
    tokens_used: int | None = None
    output_summary: str = ""


class IncidentResponse(BaseModel):
    """Full incident detail returned by the API."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    error: str
    service: str
    severity: Severity
    status: IncidentStatus
    timestamp: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    findings: list[AgentFinding] = Field(default_factory=list)
    agent_runs: list[AgentRunResponse] = Field(default_factory=list)
    recommendation: Recommendation | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentListItem(BaseModel):
    """Compact incident summary for list views."""

    id: str
    error: str
    service: str
    severity: Severity
    status: IncidentStatus
    timestamp: datetime
    created_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "0.1.0"
    environment: str = "development"

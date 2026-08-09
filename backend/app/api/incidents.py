"""Incident API endpoints.

Phase 1: In-memory store for rapid development.
Phase 4: Will be replaced with PostgreSQL persistence.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.schemas.incident import (
    ApprovalRequest,
    IncidentCreate,
    IncidentListItem,
    IncidentResponse,
    IncidentStatus,
)

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

# ── In-Memory Store (replaced by DB in Phase 4) ───────────────────────────────
_incidents: dict[str, IncidentResponse] = {}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _trigger_investigation(incident_id: str) -> None:
    """Execute the multi-agent investigation pipeline in the background."""
    incident = _incidents.get(incident_id)
    if incident:
        from app.agents.pipeline import execute_investigation_pipeline
        await execute_investigation_pipeline(incident)


# ── Endpoints ──────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new incident and trigger AI investigation",
)
async def create_incident(
    payload: IncidentCreate,
    background_tasks: BackgroundTasks,
) -> IncidentResponse:
    """Accept a production incident report and start the agent pipeline."""
    incident_id = str(uuid.uuid4())
    now = _now()

    incident = IncidentResponse(
        id=incident_id,
        error=payload.error,
        service=payload.service,
        severity=payload.severity,
        status=IncidentStatus.RECEIVED,
        timestamp=payload.timestamp or now,
        created_at=now,
        metadata=payload.metadata,
    )

    _incidents[incident_id] = incident

    # Trigger investigation in background (non-blocking)
    background_tasks.add_task(_trigger_investigation, incident_id)

    return incident


@router.get(
    "",
    response_model=list[IncidentListItem],
    summary="List all incidents",
)
async def list_incidents() -> list[IncidentListItem]:
    """Return all incidents, most recent first."""
    items = [
        IncidentListItem(
            id=inc.id,
            error=inc.error,
            service=inc.service,
            severity=inc.severity,
            status=inc.status,
            timestamp=inc.timestamp,
            created_at=inc.created_at,
        )
        for inc in _incidents.values()
    ]
    return sorted(items, key=lambda x: x.created_at, reverse=True)


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get full incident details including investigation findings",
)
async def get_incident(incident_id: str) -> IncidentResponse:
    """Return full incident detail with findings, agent runs, and recommendation."""
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )
    return incident


@router.post(
    "/{incident_id}/approve",
    response_model=IncidentResponse,
    summary="Approve the AI recommendation for an incident",
)
async def approve_incident(
    incident_id: str,
    payload: ApprovalRequest,
) -> IncidentResponse:
    """Human approves the recommended fix — triggers PR creation / Slack alert."""
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    if incident.status not in (IncidentStatus.AWAITING_APPROVAL, IncidentStatus.ANALYZED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident is in '{incident.status}' state — cannot approve",
        )

    incident.status = IncidentStatus.APPROVED
    # Phase 6: trigger GitHub PR creation / Slack notification here
    return incident


@router.post(
    "/{incident_id}/reject",
    response_model=IncidentResponse,
    summary="Reject the AI recommendation for an incident",
)
async def reject_incident(
    incident_id: str,
    payload: ApprovalRequest,
) -> IncidentResponse:
    """Human rejects the recommended fix."""
    incident = _incidents.get(incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident {incident_id} not found",
        )

    if incident.status not in (IncidentStatus.AWAITING_APPROVAL, IncidentStatus.ANALYZED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incident is in '{incident.status}' state — cannot reject",
        )

    incident.status = IncidentStatus.REJECTED
    return incident

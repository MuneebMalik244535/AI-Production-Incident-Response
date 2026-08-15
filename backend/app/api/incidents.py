"""Incident API endpoints with Enterprise Telemetry Ingestion, Remediation, and Post-Mortems."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.responses import StreamingResponse

from app.middleware.metrics import metrics_collector
from app.schemas.incident import (
    AgentFinding,
    AgentRunResponse,
    ApprovalRequest,
    IncidentCreate,
    IncidentListItem,
    IncidentResponse,
    IncidentStatus,
    Recommendation,
    Severity,
)
from app.schemas.webhooks import (
    DatadogWebhookPayload,
    PagerDutyWebhookPayload,
    PrometheusAlertmanagerPayload,
)
from app.security.sanitizer import sanitize_object, sanitize_text
from app.services.incident_memory import HistoricalIncident, search_past_incidents
from app.services.postmortem import PostMortemReport, postmortem_generator
from app.services.remediation_engine import (
    RemediationActionType,
    RemediationRequest,
    remediation_engine,
)
from app.services.streaming import publish_incident_event, stream_manager

logger = logging.getLogger("incident-platform.api")
router = APIRouter(prefix="/api/incidents", tags=["incidents"])

# ── In-Memory Store (Synchronized with DB Repository) ─────────────────────────
_incidents: dict[str, IncidentResponse] = {}


# ── Helpers ────────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _seed_initial_incidents() -> None:
    """Seed initial demo incidents if store is empty."""
    if _incidents:
        return

    now = _now()

    inc1 = IncidentResponse(
        id="INC-4821",
        service="payment-api",
        error="sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached...",
        severity=Severity.CRITICAL,
        status=IncidentStatus.AWAITING_APPROVAL,
        timestamp=now,
        created_at=now,
        findings=[
            AgentFinding(
                agent_name="Log Analysis Agent",
                finding_type="log_analysis",
                content="Analyzed 347 timeout errors & 82% connection spike in 6-minute window.",
                evidence=[{"log": "sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached"}],
                confidence=0.88,
            ),
            AgentFinding(
                agent_name="GitHub Investigation Agent",
                finding_type="github_investigation",
                content="Identified commit 8f32a1b modifying connection pool limits 14 mins before incident.",
                evidence=[{"commit": "8f32a1b", "message": "refactor payment pool release"}],
                confidence=0.92,
            ),
            AgentFinding(
                agent_name="Root Cause Agent",
                finding_type="root_cause_analysis",
                content="Database connection pool exhaustion — 10/10 connections held by stale transactions.",
                evidence=[{"cause": "Stale transaction holding pool slot"}],
                confidence=0.91,
            ),
        ],
        agent_runs=[
            AgentRunResponse(
                agent_name="Log Analysis Agent",
                status="SUCCESS",
                duration_seconds=0.04,
                tokens_used=420,
                output_summary="Analyzed 347 timeout errors & 82% connection spike in 6-minute window.",
            ),
            AgentRunResponse(
                agent_name="GitHub Investigation Agent",
                status="SUCCESS",
                duration_seconds=0.06,
                tokens_used=580,
                output_summary="Identified commit 8f32a1b modifying connection pool limits 14 mins before incident.",
            ),
            AgentRunResponse(
                agent_name="Root Cause Agent",
                status="SUCCESS",
                duration_seconds=0.03,
                tokens_used=350,
                output_summary="Deduced DB connection pool exhaustion — 10/10 connections held by stale transactions.",
            ),
            AgentRunResponse(
                agent_name="Recommendation Agent",
                status="SUCCESS",
                duration_seconds=0.04,
                tokens_used=490,
                output_summary="Risk: CRITICAL. Recommended restoring pool release() & increasing pool_size to 50.",
            ),
        ],
        recommendation=Recommendation(
            root_cause="Database connection pool exhaustion triggered by commit 8f32a1b which removed explicit connection.close() call in payment loop, causing all 10 pool slots to become permanently occupied by long-running transactions.",
            evidence=[
                "347 TimeoutError exceptions in 6-minute window (10:36–10:42 AM)",
                "Connection pool utilization: 100% at time of incident",
                "Deployment of payment-api v2.4.1 at 10:28 AM (14 min prior)",
                "Commit 8f32a1b removed pool.release() from transaction context manager",
                "Database CPU: 12% (healthy) — confirming client-side bottleneck",
            ],
            risk_level=Severity.CRITICAL,
            recommended_actions=[
                "Revert commit 8f32a1b in payment-api service (restore connection.close() call)",
                "Increase SQLAlchemy pool_size from 10 to 50 in database.py config",
                "Add pool_pre_ping=True to detect and discard stale connections at checkout",
                "Deploy hotfix as payment-api v2.4.2 with zero-downtime rolling update",
            ],
            confidence=0.91,
            suggested_pr_description="## fix: Restore DB connection pool release\n\n# Root Cause\nCommit 8f32a1b removed explicit connection.close() call, exhausting the SQLAlchemy pool (10/10 slots).\n\n# Changes\n- Restored pool release in payment loop\n- pool_size: 10 → 50\n- Added pool_pre_ping=True\n\n# Testing\n82/82 pytest tests passing ✓\nLoad test: 500 concurrent users ✓",
            requires_immediate_action=True,
        ),
    )

    inc2 = IncidentResponse(
        id="INC-4820",
        service="auth-service",
        error="JWT verification failed: signature has expired — 403 cascading on /v2/login",
        severity=Severity.CRITICAL,
        status=IncidentStatus.INVESTIGATING,
        timestamp=now,
        created_at=now,
        findings=[
            AgentFinding(
                agent_name="Log Analysis Agent",
                finding_type="log_analysis",
                content="Spike in HTTP 403 Forbidden errors across all authentication routes.",
                evidence=[{"error": "JWT expired"}],
                confidence=0.89,
            ),
        ],
        agent_runs=[
            AgentRunResponse(
                agent_name="Log Analysis Agent",
                status="SUCCESS",
                duration_seconds=0.05,
                tokens_used=310,
                output_summary="Correlated 182 authentication failures across auth-service endpoints.",
            ),
        ],
        recommendation=Recommendation(
            root_cause="RSA signing key rotation mismatched with token cache TTL, causing valid tokens to fail signature checks.",
            evidence=[
                "182 JWT verification failures logged",
                "Key rotation deployment executed at 10:35 AM",
                "Auth cache TTL was set to 60 minutes instead of 5 minutes",
            ],
            risk_level=Severity.CRITICAL,
            recommended_actions=[
                "Flush auth token redis cache",
                "Revert signing key pair to previous active version",
            ],
            confidence=0.89,
            suggested_pr_description="## fix: Flush stale auth token cache & synchronize RSA key rotation\n\n# Root Cause\nKey rotation mismatched TTL cache.",
            requires_immediate_action=True,
        ),
    )

    inc3 = IncidentResponse(
        id="INC-4819",
        service="api-gateway",
        error="HTTP 500 Internal Server Error spike — 847 errors/min on /checkout endpoint",
        severity=Severity.HIGH,
        status=IncidentStatus.RESOLVED,
        timestamp=now,
        created_at=now,
        findings=[],
        agent_runs=[],
        recommendation=Recommendation(
            root_cause="Upstream rate limiter triggered cascade failure due to unthrottled healthcheck probes.",
            evidence=["847 errors/min on /checkout endpoint"],
            risk_level=Severity.HIGH,
            recommended_actions=["Exclude healthcheck probes from rate limit counter"],
            confidence=0.95,
            suggested_pr_description="## fix: Exclude healthcheck probes from rate limiter",
            requires_immediate_action=False,
        ),
    )

    _incidents[inc1.id] = inc1
    _incidents[inc2.id] = inc2
    _incidents[inc3.id] = inc3


# Seed on module load
_seed_initial_incidents()


async def _trigger_investigation(incident_id: str) -> None:
    """Execute the multi-agent investigation pipeline in the background."""
    incident = _incidents.get(incident_id)
    if incident:
        from app.agents.pipeline import execute_investigation_pipeline
        t0 = _now()
        await execute_investigation_pipeline(incident)
        duration = (_now() - t0).total_seconds()
        metrics_collector.record_investigation(status="SUCCESS", duration=duration)


# ── Core Endpoints ─────────────────────────────────────────────────────────────


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
    """Accept a production incident report, scrub sensitive PII, and start the agent pipeline."""
    incident_id = str(uuid.uuid4())
    now = _now()

    clean_error = sanitize_text(payload.error)
    clean_meta = sanitize_object(payload.metadata)

    incident = IncidentResponse(
        id=incident_id,
        error=clean_error,
        service=payload.service.lower(),
        severity=payload.severity,
        status=IncidentStatus.RECEIVED,
        timestamp=payload.timestamp or now,
        created_at=now,
        metadata=clean_meta,
    )

    _incidents[incident_id] = incident
    metrics_collector.record_incident(service=payload.service, severity=payload.severity.value)

    # Persist initial incident to DB
    try:
        from app.db.engine import AsyncSessionLocal
        from app.db.repositories import IncidentRepository
        async with AsyncSessionLocal() as session:
            repo = IncidentRepository(session)
            await repo.create_incident(incident)
    except Exception as e:
        logger.debug(f"DB persistence note: {e}")

    # Trigger investigation in background (non-blocking)
    background_tasks.add_task(_trigger_investigation, incident_id)

    return incident


@router.post(
    "/inject",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inject a production failure and run 5-agent investigation pipeline",
)
async def inject_failure(
    payload: dict[str, str],
    background_tasks: BackgroundTasks,
) -> IncidentResponse:
    """Simulate a failure injection (db, api, auth) and trigger the investigation."""
    failure_type = payload.get("type", "db").lower()
    incident_id = f"INC-{uuid.uuid4().hex[:4].upper()}"
    now = _now()

    if failure_type == "db":
        service = "postgres-primary"
        error = "sqlalchemy.exc.TimeoutError: connection pool exhausted — 0/10 connections available"
        severity = Severity.CRITICAL
    elif failure_type == "api":
        service = "checkout-api"
        error = "HTTP 500: UnhandledPromiseRejection at /api/v2/checkout — upstream dependency timeout"
        severity = Severity.CRITICAL
    elif failure_type == "auth":
        service = "auth-service"
        error = "AuthenticationError: JWT decode failed — invalid signature algorithm RS256/HS256 mismatch"
        severity = Severity.CRITICAL
    else:
        service = payload.get("service", "custom-service")
        error = payload.get("error", "Custom failure injected")
        severity = Severity.HIGH

    clean_error = sanitize_text(error)

    incident = IncidentResponse(
        id=incident_id,
        error=clean_error,
        service=service,
        severity=severity,
        status=IncidentStatus.RECEIVED,
        timestamp=now,
        created_at=now,
        metadata={"injected": True, "type": failure_type},
    )

    _incidents[incident_id] = incident
    metrics_collector.record_incident(service=service, severity=severity.value)

    # Run investigation pipeline immediately for live injection responsiveness
    from app.agents.pipeline import execute_investigation_pipeline
    await execute_investigation_pipeline(incident)

    return incident


# ── Webhook Ingestion Endpoints (PagerDuty, Prometheus, Datadog) ────────────────


@router.post(
    "/webhook/pagerduty",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest alert from PagerDuty v2/v3 webhook",
)
async def ingest_pagerduty_alert(
    payload: PagerDutyWebhookPayload,
    background_tasks: BackgroundTasks,
) -> IncidentResponse:
    """Normalize PagerDuty alert and trigger investigation pipeline."""
    incident_create = payload.to_incident_create()
    return await create_incident(incident_create, background_tasks)


@router.post(
    "/webhook/prometheus",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest alert from Prometheus Alertmanager webhook",
)
async def ingest_prometheus_alert(
    payload: PrometheusAlertmanagerPayload,
    background_tasks: BackgroundTasks,
) -> IncidentResponse:
    """Normalize Prometheus Alertmanager alert and trigger investigation pipeline."""
    incident_create = payload.to_incident_create()
    return await create_incident(incident_create, background_tasks)


@router.post(
    "/webhook/datadog",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest alert from Datadog monitor webhook",
)
async def ingest_datadog_alert(
    payload: DatadogWebhookPayload,
    background_tasks: BackgroundTasks,
) -> IncidentResponse:
    """Normalize Datadog alert and trigger investigation pipeline."""
    incident_create = payload.to_incident_create()
    return await create_incident(incident_create, background_tasks)


# ── Incident Query Endpoints ───────────────────────────────────────────────────


@router.get(
    "",
    response_model=list[IncidentListItem],
    summary="List all incidents",
)
async def list_incidents() -> list[IncidentListItem]:
    """Return all incidents, most recent first (backed by DB with memory sync)."""
    _seed_initial_incidents()

    # Try DB load
    try:
        from app.db.engine import AsyncSessionLocal
        from app.db.repositories import IncidentRepository
        async with AsyncSessionLocal() as session:
            repo = IncidentRepository(session)
            db_items = await repo.list_incidents(limit=100)
            if db_items:
                # Merge with in-memory seeded incidents
                db_ids = {it.id for it in db_items}
                mem_items = [
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
                    if inc.id not in db_ids
                ]
                all_items = db_items + mem_items
                return sorted(all_items, key=lambda x: x.created_at, reverse=True)
    except Exception as e:
        logger.debug(f"DB list fallback: {e}")

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


# ── Incident Memory & Vector RAG Endpoint ──────────────────────────────────────


@router.get(
    "/memory/search",
    response_model=list[HistoricalIncident],
    summary="Search historical incident vector memory and runbooks",
)
async def search_memory(
    service: str = Query("", description="Target microservice name"),
    query: str = Query("", description="Error message or symptom keyword"),
    limit: int = Query(3, ge=1, le=10),
) -> list[HistoricalIncident]:
    """Retrieve similar historical incidents and verified resolutions from memory."""
    return search_past_incidents(service=service, query=query, limit=limit)


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get full incident details including investigation findings",
)
async def get_incident(incident_id: str) -> IncidentResponse:
    """Return full incident detail with findings, agent runs, and recommendation."""
    _seed_initial_incidents()

    # Check in-memory first
    incident = _incidents.get(incident_id)
    if incident:
        return incident

    # Fallback to DB
    try:
        from app.db.engine import AsyncSessionLocal
        from app.db.repositories import IncidentRepository
        async with AsyncSessionLocal() as session:
            repo = IncidentRepository(session)
            db_inc = await repo.get_by_id(incident_id)
            if db_inc:
                _incidents[incident_id] = db_inc
                return db_inc
    except Exception as e:
        logger.debug(f"DB get fallback: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Incident {incident_id} not found",
    )


# ── Approval & Remediation Endpoints ───────────────────────────────────────────


@router.post(
    "/{incident_id}/approve",
    response_model=IncidentResponse,
    summary="Approve the AI recommendation and trigger automated PR & remediation",
)
async def approve_incident(
    incident_id: str,
    payload: ApprovalRequest,
) -> IncidentResponse:
    """Human approves the recommended fix — triggers PR creation, Slack alert, and operational remediation."""
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
    metrics_collector.record_approval("APPROVE")

    # Record approval in DB if available
    try:
        from app.db.engine import AsyncSessionLocal
        from app.db.repositories import ApprovalRepository, IncidentRepository
        async with AsyncSessionLocal() as session:
            inc_repo = IncidentRepository(session)
            app_repo = ApprovalRepository(session)
            await inc_repo.update_status(incident_id, IncidentStatus.APPROVED)
            await app_repo.record_approval(
                incident_id=incident_id,
                decision=payload.decision.value,
                reviewer=payload.reviewer,
                notes=payload.notes,
                action=payload.action,
            )
    except Exception as e:
        logger.debug(f"DB approval record note: {e}")

    # Trigger GitHub PR
    from app.integrations.github_pr import create_github_pull_request
    pr_result = await create_github_pull_request(incident)
    if pr_result.get("pr_url"):
        incident.metadata["github_pr_url"] = pr_result["pr_url"]

    # Trigger Operational Remediation if specified
    remediation_result_text = "N/A"
    action_str = (payload.action or "").strip().upper()
    if action_str.startswith("REMEDIATE:") or "ROLLOUT" in action_str or "RESTART" in action_str or "CACHE" in action_str:
        action_name = action_str.replace("REMEDIATE:", "").strip()
        action_type = RemediationActionType.K8S_ROLLOUT_RESTART
        for a_type in RemediationActionType:
            if a_type.value in action_name:
                action_type = a_type
                break

        rem_req = RemediationRequest(
            action_type=action_type,
            service=incident.service,
            operator=payload.reviewer,
            incident_id=incident.id,
            dry_run=False,
        )
        rem_res = await remediation_engine.execute(rem_req)
        metrics_collector.record_remediation(action_type=action_type.value, status=rem_res.status)
        incident.metadata["remediation_status"] = rem_res.status
        incident.metadata["remediation_action"] = rem_res.action_type.value
        remediation_result_text = rem_res.output_message

    # Trigger Slack Notification
    from app.integrations.slack import send_slack_notification
    await send_slack_notification(
        title=f"Incident Approved: {incident.service}",
        text=f"Approved by {payload.reviewer}. GitHub PR: {pr_result.get('pr_url', 'N/A')}. Remediation: {remediation_result_text}",
        color="#2ea44f",
    )

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
    metrics_collector.record_approval("REJECT")

    try:
        from app.db.engine import AsyncSessionLocal
        from app.db.repositories import ApprovalRepository, IncidentRepository
        async with AsyncSessionLocal() as session:
            inc_repo = IncidentRepository(session)
            app_repo = ApprovalRepository(session)
            await inc_repo.update_status(incident_id, IncidentStatus.REJECTED)
            await app_repo.record_approval(
                incident_id=incident_id,
                decision=payload.decision.value,
                reviewer=payload.reviewer,
                notes=payload.notes,
                action="REJECTED",
            )
    except Exception as e:
        logger.debug(f"DB rejection record note: {e}")

    from app.integrations.slack import send_slack_notification
    await send_slack_notification(
        title=f"Incident Rejected: {incident.service}",
        text=f"Rejected by {payload.reviewer}. Reason: {payload.notes or 'None'}",
        color="#e94560",
    )

    return incident


# ── SRE Post-Mortem Endpoint ───────────────────────────────────────────────────


@router.get(
    "/{incident_id}/postmortem",
    response_model=PostMortemReport,
    summary="Generate an automated blameless SRE Post-Mortem report",
)
async def get_incident_postmortem(incident_id: str) -> PostMortemReport:
    """Compile a full SRE blameless post-mortem with root cause analysis, timeline, and action items."""
    incident = await get_incident(incident_id)
    return postmortem_generator.generate(incident)


# ── Real-Time Streaming Endpoints (WebSockets & SSE) ───────────────────────────


@router.websocket("/{incident_id}/ws")
async def incident_websocket(websocket: WebSocket, incident_id: str) -> None:
    """Live bidirectional WebSocket feed for agent execution events and findings."""
    await stream_manager.connect_websocket(websocket, incident_id)
    try:
        while True:
            # Keep socket open and receive any client ping/acks
            await websocket.receive_text()
    except WebSocketDisconnect:
        stream_manager.disconnect_websocket(websocket, incident_id)
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
        stream_manager.disconnect_websocket(websocket, incident_id)


@router.get(
    "/{incident_id}/events",
    summary="Server-Sent Events (SSE) stream for live agent execution",
)
async def incident_events_stream(incident_id: str) -> StreamingResponse:
    """Stream real-time agent execution events via Server-Sent Events (SSE)."""
    return StreamingResponse(
        stream_manager.sse_event_stream(incident_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


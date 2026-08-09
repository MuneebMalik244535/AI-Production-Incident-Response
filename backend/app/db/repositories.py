"""Database repository pattern for async CRUD operations."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    AgentRunModel,
    ApprovalModel,
    FindingModel,
    IncidentModel,
    RecommendationModel,
)
from app.schemas.incident import (
    AgentFinding,
    AgentRunResponse,
    IncidentListItem,
    IncidentResponse,
    IncidentStatus,
    Recommendation,
    Severity,
)


class IncidentRepository:
    """Async repository for Incident operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_incident(self, incident: IncidentResponse) -> IncidentModel:
        """Save a new incident."""
        model = IncidentModel(
            id=incident.id,
            error=incident.error,
            service=incident.service,
            severity=incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity),
            status=incident.status.value if hasattr(incident.status, "value") else str(incident.status),
            timestamp=incident.timestamp,
            created_at=incident.created_at,
            extra_metadata=incident.metadata,
        )
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def get_by_id(self, incident_id: str) -> IncidentResponse | None:
        """Fetch full incident with all runs, findings, and recommendations."""
        stmt = (
            select(IncidentModel)
            .where(IncidentModel.id == incident_id)
            .options(
                selectinload(IncidentModel.agent_runs),
                selectinload(IncidentModel.findings),
                selectinload(IncidentModel.recommendation),
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            return None

        findings = [
            AgentFinding(
                agent_name=f.agent_name,
                finding_type=f.finding_type,
                content=f.content,
                evidence=f.evidence,
                confidence=f.confidence,
            )
            for f in model.findings
        ]

        agent_runs = [
            AgentRunResponse(
                agent_name=r.agent_name,
                status=r.status,
                duration_seconds=r.duration_seconds,
                tokens_used=r.tokens_used,
                output_summary=r.output_summary,
            )
            for r in model.agent_runs
        ] if hasattr(model, "agent_runs") else []

        rec = None
        if model.recommendation:
            m_rec = model.recommendation
            rec = Recommendation(
                root_cause=m_rec.root_cause,
                evidence=m_rec.evidence,
                risk_level=Severity(m_rec.risk_level),
                recommended_actions=m_rec.recommended_actions,
                confidence=m_rec.confidence,
                suggested_pr_description=m_rec.suggested_pr_description,
                requires_immediate_action=m_rec.requires_immediate_action,
            )

        return IncidentResponse(
            id=model.id,
            error=model.error,
            service=model.service,
            severity=Severity(model.severity),
            status=IncidentStatus(model.status),
            timestamp=model.timestamp,
            created_at=model.created_at,
            findings=findings,
            agent_runs=agent_runs,
            recommendation=rec,
            metadata=model.extra_metadata or {},
        )

    async def list_all(self) -> list[IncidentListItem]:
        """List all incidents, most recent first."""
        stmt = select(IncidentModel).order_by(IncidentModel.created_at.desc())
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [
            IncidentListItem(
                id=m.id,
                error=m.error,
                service=m.service,
                severity=Severity(m.severity),
                status=IncidentStatus(m.status),
                timestamp=m.timestamp,
                created_at=m.created_at,
            )
            for m in models
        ]

    async def update_status(self, incident_id: str, new_status: IncidentStatus | str) -> None:
        """Update incident status."""
        status_str = new_status.value if hasattr(new_status, "value") else str(new_status)
        stmt = select(IncidentModel).where(IncidentModel.id == incident_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            model.status = status_str
            model.updated_at = datetime.now(timezone.utc)
            await self.session.commit()

    async def save_investigation_results(self, incident: IncidentResponse) -> None:
        """Persist agent runs, findings, and recommendation produced by the agent pipeline."""
        stmt = select(IncidentModel).where(IncidentModel.id == incident.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()

        if not model:
            return

        model.status = incident.status.value if hasattr(incident.status, "value") else str(incident.status)
        model.updated_at = datetime.now(timezone.utc)

        # Clear existing & re-add
        for r in incident.agent_runs:
            self.session.add(
                AgentRunModel(
                    incident_id=incident.id,
                    agent_name=r.agent_name,
                    status=r.status,
                    duration_seconds=r.duration_seconds,
                    tokens_used=r.tokens_used,
                    output_summary=r.output_summary,
                )
            )

        for f in incident.findings:
            self.session.add(
                FindingModel(
                    incident_id=incident.id,
                    agent_name=f.agent_name,
                    finding_type=f.finding_type,
                    content=f.content,
                    evidence=f.evidence,
                    confidence=f.confidence,
                )
            )

        if incident.recommendation:
            rec = incident.recommendation
            self.session.add(
                RecommendationModel(
                    incident_id=incident.id,
                    root_cause=rec.root_cause,
                    evidence=rec.evidence,
                    risk_level=rec.risk_level.value if hasattr(rec.risk_level, "value") else str(rec.risk_level),
                    recommended_actions=rec.recommended_actions,
                    confidence=rec.confidence,
                    suggested_pr_description=rec.suggested_pr_description,
                    requires_immediate_action=rec.requires_immediate_action,
                )
            )

        await self.session.commit()


class ApprovalRepository:
    """Async repository for Approval operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_approval(
        self,
        incident_id: str,
        decision: str,
        reviewer: str,
        notes: str = "",
        action: str = "",
    ) -> ApprovalModel:
        approval = ApprovalModel(
            incident_id=incident_id,
            decision=decision,
            reviewer=reviewer,
            notes=notes,
            action=action,
        )
        self.session.add(approval)
        await self.session.commit()
        return approval

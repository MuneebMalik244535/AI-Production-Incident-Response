"""Unit & integration tests for Database persistence layer."""

from __future__ import annotations

from datetime import datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, IncidentModel
from app.db.repositories import ApprovalRepository, IncidentRepository
from app.schemas.incident import (
    AgentFinding,
    AgentRunResponse,
    IncidentCreate,
    IncidentResponse,
    IncidentStatus,
    Recommendation,
    Severity,
)


@pytest.fixture
async def async_test_session() -> AsyncSession:
    """Create an in-memory async SQLite database session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


class TestDatabaseRepository:
    """Tests for database repositories and models."""

    @pytest.mark.asyncio
    async def test_create_and_get_incident(self, async_test_session: AsyncSession) -> None:
        repo = IncidentRepository(async_test_session)
        now = datetime.now(timezone.utc)

        incident = IncidentResponse(
            id="test-inc-100",
            error="Database connection timeout",
            service="payment-api",
            severity=Severity.CRITICAL,
            status=IncidentStatus.RECEIVED,
            timestamp=now,
            created_at=now,
            metadata={"region": "us-east-1"},
        )

        model = await repo.create_incident(incident)
        assert model.id == "test-inc-100"
        assert model.service == "payment-api"

        fetched = await repo.get_by_id("test-inc-100")
        assert fetched is not None
        assert fetched.id == "test-inc-100"
        assert fetched.error == "Database connection timeout"
        assert fetched.severity == Severity.CRITICAL

    @pytest.mark.asyncio
    async def test_list_all_incidents(self, async_test_session: AsyncSession) -> None:
        repo = IncidentRepository(async_test_session)
        now = datetime.now(timezone.utc)

        inc1 = IncidentResponse(id="inc-1", error="Err 1", service="s1", severity=Severity.LOW, status=IncidentStatus.RECEIVED, timestamp=now, created_at=now)
        inc2 = IncidentResponse(id="inc-2", error="Err 2", service="s2", severity=Severity.HIGH, status=IncidentStatus.RECEIVED, timestamp=now, created_at=now)

        await repo.create_incident(inc1)
        await repo.create_incident(inc2)

        items = await repo.list_all()
        assert len(items) == 2
        ids = [i.id for i in items]
        assert "inc-1" in ids
        assert "inc-2" in ids

    @pytest.mark.asyncio
    async def test_update_status(self, async_test_session: AsyncSession) -> None:
        repo = IncidentRepository(async_test_session)
        now = datetime.now(timezone.utc)

        inc = IncidentResponse(id="inc-status", error="Err", service="s1", severity=Severity.MEDIUM, status=IncidentStatus.RECEIVED, timestamp=now, created_at=now)
        await repo.create_incident(inc)

        await repo.update_status("inc-status", IncidentStatus.APPROVED)
        updated = await repo.get_by_id("inc-status")
        assert updated is not None
        assert updated.status == IncidentStatus.APPROVED

    @pytest.mark.asyncio
    async def test_save_investigation_results(self, async_test_session: AsyncSession) -> None:
        repo = IncidentRepository(async_test_session)
        now = datetime.now(timezone.utc)

        inc = IncidentResponse(
            id="inc-inv-res",
            error="DB failure",
            service="payment-api",
            severity=Severity.HIGH,
            status=IncidentStatus.INVESTIGATING,
            timestamp=now,
            created_at=now,
        )
        await repo.create_incident(inc)

        # Attach runs, findings, and recommendation
        inc.agent_runs.append(AgentRunResponse(agent_name="Log Agent", status="SUCCESS", duration_seconds=0.1, tokens_used=100, output_summary="Found logs"))
        inc.findings.append(AgentFinding(agent_name="Log Agent", finding_type="log_analysis", content="347 timeouts", evidence=[], confidence=0.9))
        inc.recommendation = Recommendation(root_cause="Pool exhaustion", evidence=["347 timeouts"], risk_level=Severity.CRITICAL, recommended_actions=["Increase pool size"], confidence=0.95)
        inc.status = IncidentStatus.AWAITING_APPROVAL

        await repo.save_investigation_results(inc)

        fetched = await repo.get_by_id("inc-inv-res")
        assert fetched is not None
        assert fetched.status == IncidentStatus.AWAITING_APPROVAL
        assert len(fetched.findings) == 1
        assert fetched.recommendation is not None
        assert fetched.recommendation.root_cause == "Pool exhaustion"

    @pytest.mark.asyncio
    async def test_record_approval(self, async_test_session: AsyncSession) -> None:
        inc_repo = IncidentRepository(async_test_session)
        app_repo = ApprovalRepository(async_test_session)
        now = datetime.now(timezone.utc)

        inc = IncidentResponse(id="inc-app", error="Err", service="svc", severity=Severity.LOW, status=IncidentStatus.AWAITING_APPROVAL, timestamp=now, created_at=now)
        await inc_repo.create_incident(inc)

        approval = await app_repo.record_approval(
            incident_id="inc-app",
            decision="APPROVE",
            reviewer="lead@company.com",
            notes="LGTM",
            action="create_pr",
        )
        assert approval.id is not None
        assert approval.decision == "APPROVE"
        assert approval.reviewer == "lead@company.com"

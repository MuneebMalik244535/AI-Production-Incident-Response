"""Tests for Pydantic schemas — validation, defaults, and serialization."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.incident import (
    AgentFinding,
    ApprovalDecision,
    ApprovalRequest,
    IncidentCreate,
    IncidentResponse,
    IncidentStatus,
    Recommendation,
    Severity,
)


class TestSeverityEnum:
    """Severity levels should be strictly typed."""

    def test_valid_severities(self) -> None:
        assert Severity.LOW == "LOW"
        assert Severity.MEDIUM == "MEDIUM"
        assert Severity.HIGH == "HIGH"
        assert Severity.CRITICAL == "CRITICAL"

    def test_all_levels_count(self) -> None:
        assert len(Severity) == 4


class TestIncidentStatusEnum:
    """Incident status lifecycle should have all expected states."""

    def test_all_statuses(self) -> None:
        expected = {
            "RECEIVED", "INVESTIGATING", "ANALYZED",
            "AWAITING_APPROVAL", "APPROVED", "REJECTED", "RESOLVED",
        }
        assert {s.value for s in IncidentStatus} == expected


class TestIncidentCreate:
    """Validate incident creation payloads."""

    def test_valid_payload(self) -> None:
        incident = IncidentCreate(
            error="Database connection timeout",
            service="payment-api",
            severity=Severity.CRITICAL,
        )
        assert incident.error == "Database connection timeout"
        assert incident.service == "payment-api"
        assert incident.severity == Severity.CRITICAL

    def test_timestamp_defaults_to_none(self) -> None:
        incident = IncidentCreate(
            error="Test", service="svc", severity=Severity.LOW
        )
        assert incident.timestamp is None

    def test_metadata_defaults_to_empty(self) -> None:
        incident = IncidentCreate(
            error="Test", service="svc", severity=Severity.LOW
        )
        assert incident.metadata == {}

    def test_missing_error_raises(self) -> None:
        with pytest.raises(ValidationError):
            IncidentCreate(service="svc", severity=Severity.LOW)  # type: ignore

    def test_invalid_severity_raises(self) -> None:
        with pytest.raises(ValidationError):
            IncidentCreate(
                error="Test", service="svc", severity="MEGA_CRITICAL"  # type: ignore
            )

    def test_custom_timestamp(self) -> None:
        ts = datetime(2026, 8, 1, 10, 42, 0, tzinfo=timezone.utc)
        incident = IncidentCreate(
            error="Test", service="svc", severity=Severity.HIGH, timestamp=ts
        )
        assert incident.timestamp == ts


class TestRecommendation:
    """Validate the Recommendation output schema."""

    def test_valid_recommendation(self) -> None:
        rec = Recommendation(
            root_cause="Database connection pool exhaustion",
            evidence=["347 timeout errors", "82% connection increase"],
            risk_level=Severity.CRITICAL,
            recommended_actions=[
                "Increase connection pool limit",
                "Add connection timeout",
            ],
            confidence=0.91,
            suggested_pr_description="Fix DB pool settings",
            requires_immediate_action=True,
        )
        assert rec.confidence == 0.91
        assert len(rec.recommended_actions) == 2

    def test_confidence_out_of_range_raises(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                root_cause="test",
                evidence=[],
                risk_level=Severity.LOW,
                recommended_actions=[],
                confidence=1.5,  # Invalid: must be 0-1
            )

    def test_confidence_negative_raises(self) -> None:
        with pytest.raises(ValidationError):
            Recommendation(
                root_cause="test",
                evidence=[],
                risk_level=Severity.LOW,
                recommended_actions=[],
                confidence=-0.1,  # Invalid: must be 0-1
            )


class TestAgentFinding:
    """Validate agent finding schema."""

    def test_valid_finding(self) -> None:
        finding = AgentFinding(
            agent_name="Log Analysis Agent",
            finding_type="log_analysis",
            content="Found 347 connection timeout errors in the last 30 minutes",
            evidence=[{"log_id": "log-001", "message": "Connection timeout"}],
            confidence=0.85,
        )
        assert finding.agent_name == "Log Analysis Agent"
        assert len(finding.evidence) == 1

    def test_confidence_bounds(self) -> None:
        # Exactly 0 and 1 should be valid
        f0 = AgentFinding(
            agent_name="a", finding_type="t", content="c", confidence=0.0
        )
        f1 = AgentFinding(
            agent_name="a", finding_type="t", content="c", confidence=1.0
        )
        assert f0.confidence == 0.0
        assert f1.confidence == 1.0


class TestApprovalRequest:
    """Validate approval request payloads."""

    def test_valid_approval(self) -> None:
        req = ApprovalRequest(
            decision=ApprovalDecision.APPROVE,
            reviewer="engineer@company.com",
        )
        assert req.decision == ApprovalDecision.APPROVE

    def test_valid_rejection(self) -> None:
        req = ApprovalRequest(
            decision=ApprovalDecision.REJECT,
            reviewer="senior@company.com",
            notes="Needs more analysis",
        )
        assert req.notes == "Needs more analysis"

    def test_escalate_option(self) -> None:
        req = ApprovalRequest(
            decision=ApprovalDecision.ESCALATE,
            reviewer="oncall@company.com",
        )
        assert req.decision == ApprovalDecision.ESCALATE

    def test_invalid_decision_raises(self) -> None:
        with pytest.raises(ValidationError):
            ApprovalRequest(
                decision="MAYBE",  # type: ignore
                reviewer="test@test.com",
            )

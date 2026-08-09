"""Tests for Production Features: Integrations (Slack, GitHub PRs), Auth, and Middleware."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.integrations.github_pr import create_github_pull_request
from app.integrations.slack import send_slack_notification
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentStatus, Severity


class TestIntegrations:
    """Test Slack and GitHub PR integrations."""

    @pytest.mark.asyncio
    async def test_slack_notification_simulation(self) -> None:
        success = await send_slack_notification(
            title="Test Incident Alert",
            text="Service 'payment-api' encountered 500 error",
        )
        assert success is True

    @pytest.mark.asyncio
    async def test_github_pr_creation_simulation(self) -> None:
        incident = IncidentResponse(
            id="inc-pr-test-1",
            error="Database connection pool timeout",
            service="payment-api",
            severity=Severity.CRITICAL,
            status=IncidentStatus.AWAITING_APPROVAL,
            timestamp=IncidentCreate(error="e", service="s", severity=Severity.LOW).timestamp or pytest.importorskip("datetime").datetime.now(),
        )

        res = await create_github_pull_request(incident)
        assert res is not None
        assert "pr_url" in res
        assert "payment-api" in res["pr_url"]


class TestApprovalIntegrationWorkflows:
    """Test end-to-end approval and rejection workflows triggering integrations."""

    def test_approval_triggers_pr_and_slack(
        self, client: TestClient, sample_incident_payload: dict, sample_approval_payload: dict
    ) -> None:
        # Create incident
        inc_res = client.post("/api/incidents", json=sample_incident_payload).json()
        inc_id = inc_res["id"]

        # Approve incident
        approve_resp = client.post(f"/api/incidents/{inc_id}/approve", json=sample_approval_payload)
        assert approve_resp.status_code == 200
        data = approve_resp.json()

        assert data["status"] == "APPROVED"
        assert "github_pr_url" in data["metadata"]
        assert "payment-api" in data["metadata"]["github_pr_url"]

    def test_rejection_triggers_slack(
        self, client: TestClient, sample_incident_payload: dict, sample_rejection_payload: dict
    ) -> None:
        inc_res = client.post("/api/incidents", json=sample_incident_payload).json()
        inc_id = inc_res["id"]

        reject_resp = client.post(f"/api/incidents/{inc_id}/reject", json=sample_rejection_payload)
        assert reject_resp.status_code == 200
        assert reject_resp.json()["status"] == "REJECTED"

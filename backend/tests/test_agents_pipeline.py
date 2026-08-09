"""Integration & unit tests for the OpenAI Agents SDK Multi-Agent Pipeline."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agents.github_agent import run_github_investigation
from app.agents.log_agent import run_log_analysis
from app.agents.pipeline import execute_investigation_pipeline
from app.agents.recommendation_agent import run_recommendation
from app.agents.root_cause_agent import run_root_cause_analysis
from app.schemas.incident import IncidentCreate, IncidentResponse, IncidentStatus, Severity


class TestAgentStandaloneModules:
    """Test individual agent execution modules."""

    def test_log_agent_standalone(self) -> None:
        findings = run_log_analysis(service="payment-api", error_message="Database connection timeout")
        assert findings.service == "payment-api"
        assert findings.error_count >= 1
        assert len(findings.error_patterns) >= 1
        assert findings.severity_assessment in (Severity.HIGH, Severity.CRITICAL)

    def test_github_agent_standalone(self) -> None:
        findings = run_github_investigation(service="payment-api", query="db")
        assert "payment-api" in findings.repository
        assert len(findings.suspicious_commits) >= 1
        assert "8f32a1" in findings.suspicious_commits[0]["sha"]
        assert len(findings.relevant_files) >= 1

    def test_root_cause_agent_standalone(self) -> None:
        log_f = run_log_analysis("payment-api", "Database timeout")
        gh_f = run_github_investigation("payment-api", "db")
        
        analysis = run_root_cause_analysis(log_f, gh_f)
        assert analysis.confidence >= 0.8
        assert "Database connection pool exhaustion" in analysis.root_cause
        assert len(analysis.evidence) >= 2
        assert analysis.suspected_commit is not None

    def test_recommendation_agent_standalone(self) -> None:
        log_f = run_log_analysis("payment-api", "Database timeout")
        gh_f = run_github_investigation("payment-api", "db")
        analysis = run_root_cause_analysis(log_f, gh_f)

        rec = run_recommendation(analysis)
        assert rec.risk_level == Severity.CRITICAL
        assert len(rec.recommended_actions) >= 2
        assert rec.suggested_pr_title != ""
        assert rec.requires_immediate_action is True


class TestPipelineOrchestration:
    """Test full multi-agent pipeline orchestration."""

    @pytest.mark.asyncio
    async def test_pipeline_execution(self) -> None:
        incident = IncidentResponse(
            error="Database connection timeout",
            service="payment-api",
            severity=Severity.CRITICAL,
            status=IncidentStatus.RECEIVED,
            timestamp=IncidentCreate(error="err", service="svc", severity=Severity.LOW).timestamp or pytest.importorskip("datetime").datetime.now(),
        )

        result = await execute_investigation_pipeline(incident)

        # Verify status progression
        assert result.status == IncidentStatus.AWAITING_APPROVAL

        # Verify 4 agent runs attached
        assert len(result.agent_runs) == 4
        agent_names = [run.agent_name for run in result.agent_runs]
        assert "Log Analysis Agent" in agent_names
        assert "GitHub Investigation Agent" in agent_names
        assert "Root Cause Agent" in agent_names
        assert "Recommendation Agent" in agent_names

        # Verify findings attached
        assert len(result.findings) >= 3

        # Verify final recommendation attached
        assert result.recommendation is not None
        assert result.recommendation.confidence >= 0.85
        assert len(result.recommendation.recommended_actions) >= 2
        assert result.recommendation.risk_level == Severity.CRITICAL


class TestAPIAgentIntegration:
    """Test end-to-end API incident creation + agent pipeline execution."""

    def test_api_creates_incident_and_triggers_pipeline(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        # POST incident
        resp = client.post("/api/incidents", json=sample_incident_payload)
        assert resp.status_code == 201
        inc_id = resp.json()["id"]

        # GET detail — background task should have completed pipeline execution
        detail_resp = client.get(f"/api/incidents/{inc_id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()

        assert data["status"] == "AWAITING_APPROVAL"
        assert len(data["agent_runs"]) == 4
        assert len(data["findings"]) >= 3
        assert data["recommendation"] is not None
        assert data["recommendation"]["confidence"] >= 0.8

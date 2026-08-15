"""Tests for Enterprise Production Features:

- PII & Secret Sanitization Layer
- External Webhook Alert Ingestion (PagerDuty, Prometheus, Datadog)
- Safe Operational Remediation Engine & Dry-Runs
- SRE Blameless Post-Mortem Generation
- Prometheus /metrics Exposition
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.schemas.incident import IncidentResponse, IncidentStatus, Severity
from app.security.sanitizer import sanitize_object, sanitize_text
from app.services.postmortem import postmortem_generator
from app.services.remediation_engine import (
    RemediationActionType,
    RemediationRequest,
    remediation_engine,
)


class TestSanitizer:
    """Test comprehensive secret, API key, and PII masking."""

    def test_bearer_token_redaction(self) -> None:
        raw = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        clean = sanitize_text(raw)
        assert "[REDACTED_BEARER_TOKEN]" in clean
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in clean

    def test_cloud_keys_redaction(self) -> None:
        raw = "AWS key AKIAIOSFODNN7EXAMPLE and GCP AIzaSyD-1234567890abcdef1234567890abcde"
        clean = sanitize_text(raw)
        assert "[REDACTED_AWS_ACCESS_KEY]" in clean
        assert "[REDACTED_GCP_API_KEY]" in clean
        assert "AKIAIOSFODNN7EXAMPLE" not in clean

    def test_database_url_redaction(self) -> None:
        raw = "Connecting to postgresql://postgres:SuperSecretPass123!@db.internal.corp:5432/production_db"
        clean = sanitize_text(raw)
        assert "[REDACTED_PASSWORD]" in clean
        assert "SuperSecretPass123!" not in clean
        assert "db.internal.corp:5432/production_db" in clean

    def test_email_and_credit_card_redaction(self) -> None:
        raw = "Customer user@company.com with card 4532-1234-5678-9012 failed checkout"
        clean = sanitize_text(raw)
        assert "[REDACTED_EMAIL]" in clean
        assert "[REDACTED_CREDIT_CARD]" in clean
        assert "user@company.com" not in clean
        assert "4532-1234-5678-9012" not in clean

    def test_nested_object_sanitization(self) -> None:
        payload = {
            "service": "payment-api",
            "error": "Failed with token Bearer secret_token_xyz999",
            "details": {
                "admin_email": "admin@cloud.com",
                "db_conn": "mysql://root:rootpassword@10.0.0.1:3306/db",
                "attempts": [1, 2, "error on card 4000 1234 5678 9010"],
            },
        }
        clean_obj = sanitize_object(payload)
        assert "[REDACTED_BEARER_TOKEN]" in clean_obj["error"]
        assert clean_obj["details"]["admin_email"] == "[REDACTED_EMAIL]"
        assert "[REDACTED_PASSWORD]" in clean_obj["details"]["db_conn"]
        assert "[REDACTED_CREDIT_CARD]" in clean_obj["details"]["attempts"][2]


class TestWebhookAlertIngestion:
    """Test PagerDuty, Prometheus Alertmanager, and Datadog webhook alert ingestion."""

    def test_pagerduty_webhook_ingestion(self, client: TestClient) -> None:
        payload = {
            "event": {
                "id": "pd-alert-101",
                "data": {
                    "title": "High error rate on payment-api: Database Timeout",
                    "service": {"summary": "Payment Service"},
                    "urgency": "high",
                    "html_url": "https://company.pagerduty.com/incidents/101",
                }
            }
        }
        resp = client.post("/api/incidents/webhook/pagerduty", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["service"] == "payment-service"
        assert "Database Timeout" in data["error"]
        assert data["severity"] == "CRITICAL"
        assert data["metadata"]["source"] == "PagerDuty"

    def test_prometheus_alertmanager_webhook(self, client: TestClient) -> None:
        payload = {
            "version": "4",
            "status": "firing",
            "alerts": [
                {
                    "labels": {
                        "alertname": "KubePodCrashLooping",
                        "service": "auth-service",
                        "severity": "CRITICAL",
                    },
                    "annotations": {
                        "description": "Pod auth-service-79b8f in namespace prod is crash looping",
                        "summary": "CrashLoopBackOff on auth-service",
                    },
                }
            ]
        }
        resp = client.post("/api/incidents/webhook/prometheus", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["service"] == "auth-service"
        assert "CrashLoopBackOff" in data["error"] or "crash looping" in data["error"]
        assert data["metadata"]["source"] == "PrometheusAlertmanager"

    def test_datadog_webhook(self, client: TestClient) -> None:
        payload = {
            "id": "dd-monitor-883",
            "title": "Anomaly: checkout latency p99 > 5000ms",
            "body": "Spike in checkout API latency detected across 4 pods",
            "priority": "P1",
            "tags": ["service:checkout-api", "env:production"],
        }
        resp = client.post("/api/incidents/webhook/datadog", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["service"] == "checkout-api"
        assert data["severity"] == "CRITICAL"
        assert data["metadata"]["source"] == "Datadog"


class TestOperationalRemediationEngine:
    """Test safe infrastructure remediation actions and dry-run execution."""

    @pytest.mark.asyncio
    async def test_remediation_dry_run(self) -> None:
        req = RemediationRequest(
            action_type=RemediationActionType.K8S_ROLLOUT_RESTART,
            service="payment-api",
            dry_run=True,
            operator="sre-alice",
        )
        res = await remediation_engine.execute(req)
        assert res.status == "DRY_RUN_VERIFIED"
        assert res.dry_run is True
        assert "Dry run succeeded" in res.output_message
        assert "kubectl rollout undo" in res.rollback_command

    @pytest.mark.asyncio
    async def test_remediation_k8s_rollout_undo(self) -> None:
        req = RemediationRequest(
            action_type=RemediationActionType.K8S_ROLLOUT_UNDO,
            service="payment-api",
            dry_run=False,
            operator="sre-bob",
        )
        res = await remediation_engine.execute(req)
        assert res.status == "SUCCESS"
        assert "rolled back" in res.output_message.lower()
        assert len(res.logs) >= 3

    @pytest.mark.asyncio
    async def test_remediation_flush_redis_cache(self) -> None:
        req = RemediationRequest(
            action_type=RemediationActionType.FLUSH_REDIS_CACHE,
            service="auth-service",
            parameters={"pattern": "cache:auth:*"},
            dry_run=False,
            operator="sre-charlie",
        )
        res = await remediation_engine.execute(req)
        assert res.status == "SUCCESS"
        assert "Flushed stale Redis cache" in res.output_message

    @pytest.mark.asyncio
    async def test_remediation_scale_replicas(self) -> None:
        req = RemediationRequest(
            action_type=RemediationActionType.SCALE_REPLICAS,
            service="api-gateway",
            parameters={"replicas": 10},
            dry_run=False,
            operator="sre-david",
        )
        res = await remediation_engine.execute(req)
        assert res.status == "SUCCESS"
        assert "10 replicas" in res.output_message


class TestPostMortemAndMetrics:
    """Test blameless post-mortem report generation and Prometheus metrics."""

    def test_postmortem_generation_endpoint(self, client: TestClient) -> None:
        resp = client.get("/api/incidents/INC-4821/postmortem")
        assert resp.status_code == 200
        data = resp.json()
        assert data["incident_id"] == "INC-4821"
        assert data["service"] == "payment-api"
        assert "Executive Summary" in data["markdown_report"]
        assert "Root Cause Analysis" in data["markdown_report"]
        assert len(data["timeline"]) >= 2
        assert len(data["action_items"]) >= 1

    def test_prometheus_metrics_endpoint(self, client: TestClient) -> None:
        resp = client.get("/metrics")
        assert resp.status_code == 200
        content = resp.text
        assert "incident_platform_incidents_total" in content
        assert "incident_platform_investigations_total" in content
        assert "incident_platform_avg_investigation_seconds" in content

    def test_approval_with_remediation_execution(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        # Create incident
        inc_res = client.post("/api/incidents", json=sample_incident_payload).json()
        inc_id = inc_res["id"]

        # Approve with explicit remediation action
        approval_payload = {
            "decision": "APPROVE",
            "reviewer": "sre-lead@company.com",
            "notes": "Approved rollback remediation",
            "action": "REMEDIATE:K8S_ROLLOUT_UNDO",
        }
        approve_resp = client.post(f"/api/incidents/{inc_id}/approve", json=approval_payload)
        assert approve_resp.status_code == 200
        data = approve_resp.json()
        assert data["status"] == "APPROVED"
        assert data["metadata"].get("remediation_status") == "SUCCESS"
        assert data["metadata"].get("remediation_action") == "K8S_ROLLOUT_UNDO"

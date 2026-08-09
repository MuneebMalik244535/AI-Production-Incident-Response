"""Integration tests for Payment API failure simulation and automated anomaly detection."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.services.incident_detector import detector
from app.services.payment_service.failure_injector import FailureMode, injector
from app.services.payment_service.main import app as payment_app


@pytest.fixture
def payment_client() -> TestClient:
    injector.clear()
    client = TestClient(payment_app)
    yield client
    injector.clear()


class TestPaymentServiceSimulation:
    """Test simulated Payment API endpoints and failure injection."""

    def test_payment_health(self, payment_client: TestClient) -> None:
        resp = payment_client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_payment_success(self, payment_client: TestClient) -> None:
        payload = {"amount": 49.99, "currency": "USD", "customer_id": "cust_test_01"}
        resp = payment_client.post("/pay", json=payload)
        assert resp.status_code == 200
        assert resp.json()["status"] == "success"

    def test_simulate_db_timeout_failure(self, payment_client: TestClient) -> None:
        # Set DB timeout failure mode
        payment_client.post("/simulate-failure", json={"mode": "DB_TIMEOUT", "failure_rate": 1.0})

        payload = {"amount": 99.00, "currency": "USD", "customer_id": "cust_fail_01"}
        resp = payment_client.post("/pay", json=payload)
        assert resp.status_code == 500
        assert "TimeoutError" in resp.json()["detail"]

    def test_simulate_api_failure(self, payment_client: TestClient) -> None:
        payment_client.post("/simulate-failure", json={"mode": "API_FAILURE", "failure_rate": 1.0})

        payload = {"amount": 19.99, "currency": "USD", "customer_id": "cust_fail_02"}
        resp = payment_client.post("/pay", json=payload)
        assert resp.status_code == 500
        assert "Internal Payment Gateway Error" in resp.json()["detail"]

    def test_simulate_auth_bug(self, payment_client: TestClient) -> None:
        payment_client.post("/simulate-failure", json={"mode": "AUTH_BUG", "failure_rate": 1.0})

        payload = {"amount": 5.00, "currency": "USD", "customer_id": "cust_fail_03"}
        resp = payment_client.post("/pay", json=payload)
        assert resp.status_code == 500
        assert "JWT Signature" in resp.json()["detail"]

    def test_incident_detector_spots_failure(self, payment_client: TestClient) -> None:
        # Cause failures
        payment_client.post("/simulate-failure", json={"mode": "DB_TIMEOUT", "failure_rate": 1.0})
        for _ in range(3):
            payment_client.post("/pay", json={"amount": 10.0, "currency": "USD", "customer_id": "c1"})

        incident_payload = detector.check_service_health("payment-api")
        assert incident_payload is not None
        assert incident_payload.service == "payment-api"
        assert incident_payload.severity in ("HIGH", "CRITICAL")


class TestEndToEndFailureToAIInvestigation:
    """End-to-End Test: Real failure in Payment Service -> Detection -> 5-Agent Investigation -> Recommendation."""

    def test_e2e_simulated_failure_investigation(
        self, client: TestClient, payment_client: TestClient
    ) -> None:
        # 1. Inject failure in Payment Service
        payment_client.post("/simulate-failure", json={"mode": "DB_TIMEOUT", "failure_rate": 1.0})
        
        # 2. Process payments (fails and emits real logs to Log MCP store)
        payment_client.post("/pay", json={"amount": 250.0, "currency": "USD", "customer_id": "vip_user_88"})

        # 3. Detector scans logs and builds Incident payload
        incident_create = detector.check_service_health("payment-api")
        assert incident_create is not None

        # 4. Trigger main platform API POST /api/incidents
        post_resp = client.post("/api/incidents", json=incident_create.model_dump())
        assert post_resp.status_code == 201
        inc_id = post_resp.json()["id"]

        # 5. Fetch incident details (multi-agent pipeline ran automatically)
        detail_resp = client.get(f"/api/incidents/{inc_id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()

        assert data["status"] == "AWAITING_APPROVAL"
        assert len(data["agent_runs"]) == 4
        assert len(data["findings"]) >= 3
        assert data["recommendation"] is not None
        assert "Database" in data["recommendation"]["root_cause"]

"""Tests for the Incidents API — full CRUD + approval workflow."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestCreateIncident:
    """POST /api/incidents — create and trigger investigation."""

    def test_create_incident_returns_201(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        response = client.post("/api/incidents", json=sample_incident_payload)
        assert response.status_code == 201

    def test_create_incident_returns_id(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        data = client.post("/api/incidents", json=sample_incident_payload).json()
        assert "id" in data
        assert len(data["id"]) == 36, "ID should be a UUID"

    def test_create_incident_preserves_fields(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        data = client.post("/api/incidents", json=sample_incident_payload).json()
        assert data["error"] == sample_incident_payload["error"]
        assert data["service"] == sample_incident_payload["service"]
        assert data["severity"] == sample_incident_payload["severity"]

    def test_create_incident_initial_status_is_received(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        data = client.post("/api/incidents", json=sample_incident_payload).json()
        assert data["status"] == "RECEIVED"

    def test_create_incident_with_metadata(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        data = client.post("/api/incidents", json=sample_incident_payload).json()
        assert data["metadata"]["region"] == "us-east-1"
        assert data["metadata"]["request_id"] == "req-abc-123"

    def test_create_incident_without_timestamp_uses_default(
        self, client: TestClient
    ) -> None:
        payload = {
            "error": "Test error",
            "service": "test-service",
            "severity": "LOW",
        }
        data = client.post("/api/incidents", json=payload).json()
        assert data["timestamp"] is not None

    def test_create_incident_invalid_severity_returns_422(
        self, client: TestClient
    ) -> None:
        payload = {
            "error": "Test error",
            "service": "test-service",
            "severity": "INVALID_LEVEL",
        }
        response = client.post("/api/incidents", json=payload)
        assert response.status_code == 422

    def test_create_incident_missing_required_fields_returns_422(
        self, client: TestClient
    ) -> None:
        response = client.post("/api/incidents", json={})
        assert response.status_code == 422

    def test_create_multiple_incidents_unique_ids(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        resp1 = client.post("/api/incidents", json=sample_incident_payload).json()
        resp2 = client.post("/api/incidents", json=sample_incident_payload).json()
        assert resp1["id"] != resp2["id"]


class TestListIncidents:
    """GET /api/incidents — list all incidents."""

    def test_list_empty(self, client: TestClient) -> None:
        response = client.get("/api/incidents")
        assert response.status_code == 200
        # Note: may have incidents from other tests since in-memory store
        # is shared within the same app instance
        assert isinstance(response.json(), list)

    def test_list_after_create(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        # Create an incident
        created = client.post("/api/incidents", json=sample_incident_payload).json()

        # List should contain it
        incidents = client.get("/api/incidents").json()
        ids = [i["id"] for i in incidents]
        assert created["id"] in ids

    def test_list_returns_compact_items(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        client.post("/api/incidents", json=sample_incident_payload)
        incidents = client.get("/api/incidents").json()

        for item in incidents:
            assert "id" in item
            assert "error" in item
            assert "service" in item
            assert "severity" in item
            assert "status" in item
            # List items should NOT contain full findings
            assert "findings" not in item
            assert "recommendation" not in item


class TestGetIncident:
    """GET /api/incidents/{id} — get full incident details."""

    def test_get_existing_incident(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        created = client.post("/api/incidents", json=sample_incident_payload).json()

        response = client.get(f"/api/incidents/{created['id']}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == created["id"]
        assert data["error"] == sample_incident_payload["error"]

    def test_get_nonexistent_incident_returns_404(
        self, client: TestClient
    ) -> None:
        response = client.get("/api/incidents/nonexistent-id-12345")
        assert response.status_code == 404

    def test_get_incident_contains_full_detail(
        self, client: TestClient, sample_incident_payload: dict
    ) -> None:
        created = client.post("/api/incidents", json=sample_incident_payload).json()
        data = client.get(f"/api/incidents/{created['id']}").json()

        # Full detail should include these fields
        assert "findings" in data
        assert "agent_runs" in data
        assert "recommendation" in data
        assert "metadata" in data


class TestApproveIncident:
    """POST /api/incidents/{id}/approve — human approval workflow."""

    def _create_and_set_status(
        self, client: TestClient, payload: dict, target_status: str
    ) -> str:
        """Helper: create an incident and manually set its status for testing."""
        from app.api.incidents import _incidents

        created = client.post("/api/incidents", json=payload).json()
        incident_id = created["id"]
        # Directly mutate in-memory store for test setup
        _incidents[incident_id].status = target_status
        return incident_id

    def test_approve_analyzed_incident(
        self,
        client: TestClient,
        sample_incident_payload: dict,
        sample_approval_payload: dict,
    ) -> None:
        incident_id = self._create_and_set_status(
            client, sample_incident_payload, "ANALYZED"
        )

        response = client.post(
            f"/api/incidents/{incident_id}/approve",
            json=sample_approval_payload,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "APPROVED"

    def test_approve_awaiting_approval_incident(
        self,
        client: TestClient,
        sample_incident_payload: dict,
        sample_approval_payload: dict,
    ) -> None:
        incident_id = self._create_and_set_status(
            client, sample_incident_payload, "AWAITING_APPROVAL"
        )

        response = client.post(
            f"/api/incidents/{incident_id}/approve",
            json=sample_approval_payload,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "APPROVED"

    def test_approve_received_incident_returns_400(
        self,
        client: TestClient,
        sample_incident_payload: dict,
        sample_approval_payload: dict,
    ) -> None:
        created = client.post("/api/incidents", json=sample_incident_payload).json()

        response = client.post(
            f"/api/incidents/{created['id']}/approve",
            json=sample_approval_payload,
        )
        assert response.status_code == 400

    def test_approve_nonexistent_returns_404(
        self, client: TestClient, sample_approval_payload: dict
    ) -> None:
        response = client.post(
            "/api/incidents/fake-id-999/approve",
            json=sample_approval_payload,
        )
        assert response.status_code == 404


class TestRejectIncident:
    """POST /api/incidents/{id}/reject — human rejection workflow."""

    def _create_and_set_status(
        self, client: TestClient, payload: dict, target_status: str
    ) -> str:
        from app.api.incidents import _incidents

        created = client.post("/api/incidents", json=payload).json()
        incident_id = created["id"]
        _incidents[incident_id].status = target_status
        return incident_id

    def test_reject_analyzed_incident(
        self,
        client: TestClient,
        sample_incident_payload: dict,
        sample_rejection_payload: dict,
    ) -> None:
        incident_id = self._create_and_set_status(
            client, sample_incident_payload, "ANALYZED"
        )

        response = client.post(
            f"/api/incidents/{incident_id}/reject",
            json=sample_rejection_payload,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "REJECTED"

    def test_reject_nonexistent_returns_404(
        self, client: TestClient, sample_rejection_payload: dict
    ) -> None:
        response = client.post(
            "/api/incidents/fake-id-999/reject",
            json=sample_rejection_payload,
        )
        assert response.status_code == 404

    def test_reject_already_approved_returns_400(
        self,
        client: TestClient,
        sample_incident_payload: dict,
        sample_rejection_payload: dict,
    ) -> None:
        incident_id = self._create_and_set_status(
            client, sample_incident_payload, "APPROVED"
        )

        response = client.post(
            f"/api/incidents/{incident_id}/reject",
            json=sample_rejection_payload,
        )
        assert response.status_code == 400

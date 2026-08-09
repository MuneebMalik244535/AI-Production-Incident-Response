"""Tests for the health check endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Health check should always return system status."""

    def test_health_returns_200(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_body(self, client: TestClient) -> None:
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "environment" in data

    def test_health_version_format(self, client: TestClient) -> None:
        data = client.get("/health").json()
        parts = data["version"].split(".")
        assert len(parts) == 3, "Version should be semver (x.y.z)"

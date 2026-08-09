"""Pytest configuration and shared fixtures for the test suite."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a fresh test client for each test.

    Uses the synchronous TestClient (no need for httpx async client
    since our endpoints are lightweight).
    """
    return TestClient(app)


@pytest.fixture
def sample_incident_payload() -> dict:
    """Standard incident payload for testing."""
    return {
        "error": "Database connection timeout",
        "service": "payment-api",
        "severity": "CRITICAL",
        "metadata": {
            "region": "us-east-1",
            "request_id": "req-abc-123",
        },
    }


@pytest.fixture
def sample_incident_low() -> dict:
    """Low severity incident for testing."""
    return {
        "error": "Slow response time on /api/users endpoint",
        "service": "user-service",
        "severity": "LOW",
        "metadata": {},
    }


@pytest.fixture
def sample_approval_payload() -> dict:
    """Standard approval payload."""
    return {
        "decision": "APPROVE",
        "reviewer": "engineer@company.com",
        "notes": "Looks correct, proceed with the fix.",
        "action": "create_pr",
    }


@pytest.fixture
def sample_rejection_payload() -> dict:
    """Standard rejection payload."""
    return {
        "decision": "REJECT",
        "reviewer": "senior-engineer@company.com",
        "notes": "Root cause analysis seems incomplete. Needs manual review.",
    }

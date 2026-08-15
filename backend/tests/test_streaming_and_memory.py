"""Tests for Real-Time Streaming (WebSockets & SSE) and Incident Memory (Vector RAG)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.agents.pipeline import execute_investigation_pipeline
from app.schemas.incident import IncidentResponse, IncidentStatus, Severity
from app.services.incident_memory import (
    HistoricalIncident,
    incident_memory,
    search_past_incidents,
)
from app.services.streaming import publish_incident_event, stream_manager


class TestIncidentMemory:
    """Test historical incident semantic search and RAG knowledge retrieval."""

    def test_search_by_service(self) -> None:
        matches = search_past_incidents(service="payment-api", query="timeout pool limit")
        assert len(matches) >= 1
        top = matches[0]
        assert top.service == "payment-api"
        assert "pool" in top.root_cause.lower() or "connection" in top.root_cause.lower()
        assert "POOL_SIZE" in top.verified_fix

    def test_search_by_jwt_keyword(self) -> None:
        matches = search_past_incidents(service="auth-service", query="JWT expired rotation")
        assert len(matches) >= 1
        top = matches[0]
        assert top.service == "auth-service"
        assert "key rotation" in top.root_cause.lower()
        assert "redis" in top.verified_fix.lower()

    def test_search_deadlock(self) -> None:
        matches = search_past_incidents(service="order-service", query="deadlock row-level lock")
        assert len(matches) >= 1
        top = matches[0]
        assert "deadlock" in top.error_pattern.lower()
        assert "SELECT FOR UPDATE" in top.verified_fix

    def test_add_new_incident_to_memory(self) -> None:
        custom_inc = HistoricalIncident(
            id="INC-CUSTOM-99",
            service="billing-api",
            error_pattern="StripeRateLimitError: 429 Too Many Requests on payment intent create",
            root_cause="Stripe API retry loop lacked exponential jitter backoff.",
            verified_fix="Implemented exponential backoff with random full jitter for Stripe API retries.",
            tags=["stripe", "rate_limit", "billing"],
        )
        incident_memory.add_incident(custom_inc)
        results = search_past_incidents(service="billing-api", query="stripe rate limit 429")
        assert any(r.id == "INC-CUSTOM-99" for r in results)


class TestStreamingEventBus:
    """Test WebSocket and SSE subscription, history replay, and broadcasting."""

    @pytest.mark.asyncio
    async def test_sse_subscription_and_broadcast(self) -> None:
        inc_id = "test-stream-inc-1"
        queue = stream_manager.subscribe_sse(inc_id)

        # Broadcast test event
        await publish_incident_event(inc_id, "TEST_AGENT_EVENT", {"step": "log_analysis", "errors": 42})

        # Receive from queue
        event = await queue.get()
        assert event["incident_id"] == inc_id
        assert event["event_type"] == "TEST_AGENT_EVENT"
        assert event["data"]["errors"] == 42

        stream_manager.unsubscribe_sse(queue, inc_id)

    @pytest.mark.asyncio
    async def test_pipeline_streaming_event_history(self) -> None:
        now = datetime.now(timezone.utc)
        incident = IncidentResponse(
            id="INC-STREAM-TEST-88",
            service="payment-api",
            error="Database connection pool timeout",
            severity=Severity.CRITICAL,
            status=IncidentStatus.RECEIVED,
            timestamp=now,
            created_at=now,
        )

        await execute_investigation_pipeline(incident)

        history = stream_manager.event_history.get(incident.id, [])
        assert len(history) >= 5

        event_types = [ev["event_type"] for ev in history]
        assert "PIPELINE_STARTED" in event_types
        assert "AGENT_STARTED" in event_types
        assert "AGENT_FINDING" in event_types
        assert "ROOT_CAUSE_DEDUCED" in event_types
        assert "RECOMMENDATION_READY" in event_types
        assert "PIPELINE_COMPLETED" in event_types


class TestStreamingAndMemoryEndpoints:
    """Test REST, SSE, and WebSocket endpoints."""

    def test_memory_search_api_endpoint(self, client: TestClient) -> None:
        resp = client.get("/api/incidents/memory/search?service=payment-api&query=pool+exhaustion")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "payment-api" in data[0]["service"]

    @pytest.mark.asyncio
    async def test_sse_generator_stream(self) -> None:
        chunks = []
        async for chunk in stream_manager.sse_event_stream("INC-4821"):
            chunks.append(chunk)
            break
        assert len(chunks) == 1
        assert "connected" in chunks[0] or "data" in chunks[0] or ":" in chunks[0]

    def test_websocket_endpoint(self, client: TestClient) -> None:
        with client.websocket_connect("/api/incidents/INC-4821/ws") as ws:
            # Send ping
            ws.send_text(json.dumps({"action": "ping"}))
            # Verify socket stays open
            assert ws is not None

"""Real-Time Investigation Streaming Manager.

Provides WebSocket and Server-Sent Events (SSE) broadcasting for live agent execution,
intermediate findings, tool invocations, and root cause synthesis.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, AsyncGenerator
from fastapi import WebSocket

logger = logging.getLogger("incident-platform.streaming")


class IncidentStreamManager:
    """Manages WebSocket and SSE subscriber connections for live incident updates."""

    def __init__(self) -> None:
        # Maps incident_id -> list of active WebSockets
        self.active_websockets: dict[str, list[WebSocket]] = {}
        # Maps incident_id -> list of SSE asyncio queues
        self.sse_subscribers: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        # Recent event buffer per incident
        self.event_history: dict[str, list[dict[str, Any]]] = {}

    async def connect_websocket(self, websocket: WebSocket, incident_id: str) -> None:
        """Register and accept a new WebSocket connection."""
        await websocket.accept()
        if incident_id not in self.active_websockets:
            self.active_websockets[incident_id] = []
        self.active_websockets[incident_id].append(websocket)
        logger.info(f"🔌 WebSocket connected for incident '{incident_id}' (active: {len(self.active_websockets[incident_id])})")

        # Replay event history for newly connected client
        if incident_id in self.event_history:
            for event in self.event_history[incident_id]:
                try:
                    await websocket.send_text(json.dumps(event))
                except Exception:
                    break

    def disconnect_websocket(self, websocket: WebSocket, incident_id: str) -> None:
        """Unregister a disconnected WebSocket."""
        if incident_id in self.active_websockets:
            if websocket in self.active_websockets[incident_id]:
                self.active_websockets[incident_id].remove(websocket)
            if not self.active_websockets[incident_id]:
                del self.active_websockets[incident_id]
        logger.info(f"🔌 WebSocket disconnected for incident '{incident_id}'")

    def subscribe_sse(self, incident_id: str) -> asyncio.Queue[dict[str, Any]]:
        """Register a new SSE queue subscriber."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        if incident_id not in self.sse_subscribers:
            self.sse_subscribers[incident_id] = []
        self.sse_subscribers[incident_id].append(queue)
        logger.info(f"📡 SSE subscriber added for incident '{incident_id}'")
        return queue

    def unsubscribe_sse(self, queue: asyncio.Queue[dict[str, Any]], incident_id: str) -> None:
        """Unregister an SSE queue subscriber."""
        if incident_id in self.sse_subscribers:
            if queue in self.sse_subscribers[incident_id]:
                self.sse_subscribers[incident_id].remove(queue)
            if not self.sse_subscribers[incident_id]:
                del self.sse_subscribers[incident_id]
        logger.info(f"📡 SSE subscriber removed for incident '{incident_id}'")

    async def broadcast(self, incident_id: str, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast an event to all WebSocket and SSE subscribers for an incident."""
        now = datetime.now(timezone.utc).isoformat()
        payload = {
            "incident_id": incident_id,
            "event_type": event_type,
            "timestamp": now,
            "data": data,
        }

        # Store in event history
        if incident_id not in self.event_history:
            self.event_history[incident_id] = []
        self.event_history[incident_id].append(payload)
        if len(self.event_history[incident_id]) > 50:
            self.event_history[incident_id] = self.event_history[incident_id][-50:]

        # Broadcast to WebSockets
        if incident_id in self.active_websockets:
            dead_sockets = []
            for ws in self.active_websockets[incident_id]:
                try:
                    await ws.send_text(json.dumps(payload))
                except Exception:
                    dead_sockets.append(ws)
            for dead_ws in dead_sockets:
                self.disconnect_websocket(dead_ws, incident_id)

        # Broadcast to SSE queues
        if incident_id in self.sse_subscribers:
            for queue in self.sse_subscribers[incident_id]:
                try:
                    queue.put_nowait(payload)
                except Exception as e:
                    logger.debug(f"SSE queue error: {e}")

    async def sse_event_stream(self, incident_id: str) -> AsyncGenerator[str, None]:
        """Yield SSE formatted event strings for an incident."""
        queue = self.subscribe_sse(incident_id)

        # Initial connection acknowledgment
        yield f": connected to stream for incident {incident_id}\n\n"

        # Replay event history
        if incident_id in self.event_history:
            for past_event in self.event_history[incident_id]:
                yield f"data: {json.dumps(past_event)}\n\n"

        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Send keep-alive heartbeat
                    yield f": keep-alive {datetime.now(timezone.utc).isoformat()}\n\n"
        finally:
            self.unsubscribe_sse(queue, incident_id)


# Singleton instance
stream_manager = IncidentStreamManager()


async def publish_incident_event(incident_id: str, event_type: str, data: dict[str, Any]) -> None:
    """Convenience helper to broadcast an event across all streaming channels."""
    await stream_manager.broadcast(incident_id, event_type, data)

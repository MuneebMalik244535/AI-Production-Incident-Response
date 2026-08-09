"""MCP Server exposing tools for log searching, retrieval, and error analysis.

Can run standalone via stdio (`mcp run app/mcp_servers/log_server.py`) or programmatically.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP
from app.mcp_servers.schemas import ErrorSummary, LogEntry

# Initialize FastMCP Server
mcp = FastMCP(
    "LogAnalysisServer",
    instructions="Provides tools to query logs, retrieve error details, and generate error summaries for production services.",
)

# ── Log Store Initialization (Mock + In-memory store) ──────────────────────────
# Pre-populate realistic initial logs so tests & standalone MCP tools work out-of-the-box

def _generate_mock_logs() -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    mock_data = [
        {
            "id": "log-db-timeout-101",
            "service": "payment-api",
            "severity": "CRITICAL",
            "message": "sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 30.00",
            "timestamp": (now - timedelta(minutes=15)).isoformat(),
            "metadata": {"endpoint": "/api/v1/payments", "db_pool_size": 10, "active_connections": 20},
            "stack_trace": (
                "Traceback (most recent call last):\n"
                "  File '/app/routes/payment.py', line 45, in process_payment\n"
                "    conn = db.get_connection()\n"
                "sqlalchemy.exc.TimeoutError: QueuePool limit reached"
            ),
        },
        {
            "id": "log-db-timeout-102",
            "service": "payment-api",
            "severity": "ERROR",
            "message": "Database connection pool exhaustion detected. 347 requests waiting for DB connection.",
            "timestamp": (now - timedelta(minutes=12)).isoformat(),
            "metadata": {"endpoint": "/api/v1/payments", "waiting_requests": 347},
            "stack_trace": None,
        },
        {
            "id": "log-auth-fail-201",
            "service": "auth-service",
            "severity": "ERROR",
            "message": "JWT Signature verification failed for token header kid=auth-key-99",
            "timestamp": (now - timedelta(minutes=30)).isoformat(),
            "metadata": {"user_id": "usr-883", "ip": "192.168.1.45"},
            "stack_trace": None,
        },
        {
            "id": "log-gateway-500-301",
            "service": "api-gateway",
            "severity": "HIGH",
            "message": "Upstream service 'payment-api' responded with HTTP 504 Gateway Timeout",
            "timestamp": (now - timedelta(minutes=10)).isoformat(),
            "metadata": {"latency_ms": 30005, "status_code": 504},
            "stack_trace": None,
        },
    ]
    return mock_data


_LOG_STORE: list[dict[str, Any]] = _generate_mock_logs()


def add_log_entry(
    service: str,
    severity: str,
    message: str,
    metadata: dict[str, Any] | None = None,
    stack_trace: str | None = None,
) -> dict[str, Any]:
    """Helper to add log entries dynamically (used by tests & log ingestion)."""
    entry = {
        "id": f"log-{uuid.uuid4().hex[:8]}",
        "service": service.lower(),
        "severity": severity.upper(),
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
        "stack_trace": stack_trace,
    }
    _LOG_STORE.append(entry)
    return entry


# ── MCP Tools ─────────────────────────────────────────────────────────────────


@mcp.tool()
def search_logs(
    service: str = "",
    severity: str = "",
    time_range_minutes: int = 60,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search application logs by service name, severity, and time window.

    Args:
        service: Name of service (e.g., 'payment-api', 'auth-service'). Empty matches all.
        severity: Log severity level ('CRITICAL', 'ERROR', 'WARNING', 'INFO'). Empty matches all.
        time_range_minutes: Filter logs from the last N minutes. Default 60.
        limit: Max number of log entries to return. Default 50.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=time_range_minutes)
    results = []

    for item in reversed(_LOG_STORE):
        try:
            item_ts = datetime.fromisoformat(item["timestamp"])
        except ValueError:
            continue

        if item_ts < cutoff:
            continue

        if service and item["service"].lower() != service.lower():
            continue

        if severity and item["severity"].upper() != severity.upper():
            continue

        results.append(item)
        if len(results) >= limit:
            break

    return results


@mcp.tool()
def get_log_entry(log_id: str) -> dict[str, Any]:
    """Retrieve detailed information for a specific log entry by its ID.

    Args:
        log_id: The unique log entry identifier (e.g. 'log-db-timeout-101').
    """
    for entry in _LOG_STORE:
        if entry["id"] == log_id:
            return entry

    return {"error": f"Log entry '{log_id}' not found"}


@mcp.tool()
def get_error_summary(service: str, time_range_minutes: int = 60) -> dict[str, Any]:
    """Aggregate error counts and identify error spikes for a specific service.

    Args:
        service: Service name to analyze (e.g., 'payment-api').
        time_range_minutes: Time window in minutes to analyze. Default 60.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=time_range_minutes)
    matching_logs = []
    severity_counts: dict[str, int] = {}
    message_counts: dict[str, int] = {}

    for item in _LOG_STORE:
        try:
            item_ts = datetime.fromisoformat(item["timestamp"])
        except ValueError:
            continue

        if item_ts >= cutoff and item["service"].lower() == service.lower():
            matching_logs.append(item)
            sev = item["severity"].upper()
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

            msg_key = item["message"][:80]
            message_counts[msg_key] = message_counts.get(msg_key, 0) + 1

    top_errors = [
        {"message": msg, "count": count}
        for msg, count in sorted(message_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    total_errors = len(matching_logs)
    spike_detected = total_errors >= 2  # simple threshold for mock

    summary = ErrorSummary(
        service=service,
        time_range_minutes=time_range_minutes,
        total_errors=total_errors,
        error_counts_by_severity=severity_counts,
        top_error_messages=top_errors,
        spike_detected=spike_detected,
        increase_percentage=82.0 if spike_detected else 0.0,
    )
    return summary.model_dump()


if __name__ == "__main__":
    mcp.run()

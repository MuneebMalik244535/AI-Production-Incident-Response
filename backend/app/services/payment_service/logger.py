"""Structured logger for simulated Payment API that feeds logs to the Log MCP store."""

from __future__ import annotations

import logging
from typing import Any

from app.mcp_servers.log_server import add_log_entry

logger = logging.getLogger("payment-service")


def log_payment_event(
    severity: str,
    message: str,
    metadata: dict[str, Any] | None = None,
    stack_trace: str | None = None,
) -> dict[str, Any]:
    """Emit structured log event to console & Log MCP Server store."""
    metadata = metadata or {}
    
    # Emit to standard logger
    log_msg = f"[PaymentAPI] {severity} - {message}"
    if severity == "CRITICAL":
        logger.critical(log_msg)
    elif severity == "ERROR":
        logger.error(log_msg)
    else:
        logger.info(log_msg)

    # Ingest into Log MCP server store for agent inspection
    return add_log_entry(
        service="payment-api",
        severity=severity,
        message=message,
        metadata=metadata,
        stack_trace=stack_trace,
    )

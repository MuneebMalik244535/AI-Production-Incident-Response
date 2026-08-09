"""Automated Incident Detector that monitors logs and triggers AI investigations."""

from __future__ import annotations

import logging
from typing import Any

from app.mcp_servers.log_server import get_error_summary
from app.schemas.incident import IncidentCreate, Severity

logger = logging.getLogger("incident-platform.detector")


class IncidentDetector:
    """Monitors logs and detects anomalies or error spikes."""

    def __init__(self, error_threshold: int = 2) -> None:
        self.error_threshold = error_threshold

    def check_service_health(self, service: str = "payment-api") -> IncidentCreate | None:
        """Scan logs for error spikes and return an IncidentCreate payload if detected."""
        summary = get_error_summary(service=service, time_range_minutes=30)
        total_errors = summary.get("total_errors", 0)

        if total_errors >= self.error_threshold:
            top_msgs = summary.get("top_error_messages", [])
            primary_error = top_msgs[0]["message"] if top_msgs else "High error rate detected"
            
            severity = Severity.CRITICAL if "timeout" in primary_error.lower() or "memory" in primary_error.lower() else Severity.HIGH

            logger.info(f"🚨 Anomaly Detected on '{service}': {total_errors} errors. Primary error: '{primary_error}'")

            return IncidentCreate(
                error=primary_error,
                service=service,
                severity=severity,
                metadata={
                    "total_errors": total_errors,
                    "spike_detected": summary.get("spike_detected", True),
                    "source": "AutomatedIncidentDetector",
                },
            )

        return None


# Singleton instance
detector = IncidentDetector()

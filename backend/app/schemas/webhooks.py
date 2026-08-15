"""Enterprise Alert Ingestion Webhook Schemas.

Supports payload normalization for PagerDuty, Prometheus Alertmanager, and Datadog.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from app.schemas.incident import IncidentCreate, Severity


class PagerDutyWebhookPayload(BaseModel):
    """PagerDuty v2 Webhook event payload."""

    event: dict[str, Any] = Field(default_factory=dict)
    messages: list[dict[str, Any]] = Field(default_factory=list)

    def to_incident_create(self) -> IncidentCreate:
        """Convert PagerDuty alert to standardized IncidentCreate."""
        # Handle v2 webhook or webhook v3 payload
        data = self.event.get("data", {}) if self.event else (self.messages[0] if self.messages else {})
        title = data.get("title") or data.get("summary") or "PagerDuty Alert Triggered"
        service_info = data.get("service", {})
        service_name = service_info.get("summary") or service_info.get("name") or "production-service"
        urgency = data.get("urgency", "high").lower()

        severity = Severity.CRITICAL if urgency in ("high", "critical", "sev1") else Severity.HIGH

        return IncidentCreate(
            error=title,
            service=service_name.lower().replace(" ", "-"),
            severity=severity,
            metadata={
                "source": "PagerDuty",
                "pagerduty_id": data.get("id", ""),
                "html_url": data.get("html_url", ""),
            },
        )


class PrometheusAlertmanagerPayload(BaseModel):
    """Prometheus Alertmanager webhook event payload."""

    version: str = "4"
    groupKey: str = ""
    status: str = "firing"
    receiver: str = "incident-platform"
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    commonLabels: dict[str, str] = Field(default_factory=dict)
    commonAnnotations: dict[str, str] = Field(default_factory=dict)

    def to_incident_create(self) -> IncidentCreate:
        """Convert Prometheus Alertmanager alert to standardized IncidentCreate."""
        first_alert = self.alerts[0] if self.alerts else {}
        labels = first_alert.get("labels", self.commonLabels)
        annotations = first_alert.get("annotations", self.commonAnnotations)

        alert_name = labels.get("alertname", "PrometheusAlert")
        description = annotations.get("description") or annotations.get("summary") or f"Prometheus alert firing: {alert_name}"
        service = labels.get("service") or labels.get("job") or labels.get("app") or "k8s-service"
        raw_sev = labels.get("severity", "critical").upper()

        sev_map = {
            "CRITICAL": Severity.CRITICAL,
            "ERROR": Severity.CRITICAL,
            "WARNING": Severity.HIGH,
            "INFO": Severity.MEDIUM,
        }
        severity = sev_map.get(raw_sev, Severity.HIGH)

        return IncidentCreate(
            error=description,
            service=service.lower(),
            severity=severity,
            metadata={
                "source": "PrometheusAlertmanager",
                "alertname": alert_name,
                "status": self.status,
                "labels": labels,
                "annotations": annotations,
            },
        )


class DatadogWebhookPayload(BaseModel):
    """Datadog monitor webhook payload."""

    id: str = ""
    title: str = "Datadog Alert Triggered"
    body: str = ""
    event_type: str = "metric_alert"
    priority: str = "P1"
    tags: list[str] = Field(default_factory=list)

    def to_incident_create(self) -> IncidentCreate:
        """Convert Datadog alert to standardized IncidentCreate."""
        service = "datadog-service"
        for tag in self.tags:
            if tag.startswith("service:"):
                service = tag.split(":", 1)[1]
                break

        severity = Severity.CRITICAL if self.priority in ("P1", "P2", "normal") else Severity.HIGH

        return IncidentCreate(
            error=self.body or self.title,
            service=service.lower(),
            severity=severity,
            metadata={
                "source": "Datadog",
                "monitor_id": self.id,
                "title": self.title,
                "priority": self.priority,
            },
        )

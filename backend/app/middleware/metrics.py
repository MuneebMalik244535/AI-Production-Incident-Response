"""Prometheus Metrics Collector and Exposition for Incident Platform."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any


class MetricsCollector:
    """Thread-safe Prometheus metrics collector for SRE observability."""

    def __init__(self) -> None:
        self.incidents_total: dict[tuple[str, str], int] = defaultdict(int)
        self.investigations_total: dict[str, int] = defaultdict(int)
        self.approvals_total: dict[str, int] = defaultdict(int)
        self.remediations_total: dict[tuple[str, str], int] = defaultdict(int)
        self.pipeline_durations: list[float] = []

    def record_incident(self, service: str, severity: str) -> None:
        self.incidents_total[(service, severity)] += 1

    def record_investigation(self, status: str, duration: float) -> None:
        self.investigations_total[status] += 1
        self.pipeline_durations.append(duration)
        if len(self.pipeline_durations) > 1000:
            self.pipeline_durations = self.pipeline_durations[-1000:]

    def record_approval(self, decision: str) -> None:
        self.approvals_total[decision] += 1

    def record_remediation(self, action_type: str, status: str) -> None:
        self.remediations_total[(action_type, status)] += 1

    def export_prometheus(self) -> str:
        """Export metrics in standard Prometheus exposition text format."""
        lines = [
            "# HELP incident_platform_incidents_total Total number of incidents created or ingested.",
            "# TYPE incident_platform_incidents_total counter",
        ]
        for (service, severity), count in self.incidents_total.items():
            lines.append(f'incident_platform_incidents_total{{service="{service}",severity="{severity}"}} {count}')

        lines.extend([
            "# HELP incident_platform_investigations_total Total agent investigation pipelines executed.",
            "# TYPE incident_platform_investigations_total counter",
        ])
        for status, count in self.investigations_total.items():
            lines.append(f'incident_platform_investigations_total{{status="{status}"}} {count}')

        lines.extend([
            "# HELP incident_platform_approvals_total Total approvals or rejections processed.",
            "# TYPE incident_platform_approvals_total counter",
        ])
        for decision, count in self.approvals_total.items():
            lines.append(f'incident_platform_approvals_total{{decision="{decision}"}} {count}')

        lines.extend([
            "# HELP incident_platform_remediations_total Total operational remediation actions executed.",
            "# TYPE incident_platform_remediations_total counter",
        ])
        for (action, status), count in self.remediations_total.items():
            lines.append(f'incident_platform_remediations_total{{action="{action}",status="{status}"}} {count}')

        avg_duration = sum(self.pipeline_durations) / len(self.pipeline_durations) if self.pipeline_durations else 0.0
        lines.extend([
            "# HELP incident_platform_avg_investigation_seconds Average agent investigation duration in seconds.",
            "# TYPE incident_platform_avg_investigation_seconds gauge",
            f"incident_platform_avg_investigation_seconds {avg_duration:.3f}",
        ])

        return "\n".join(lines) + "\n"


# Singleton instance
metrics_collector = MetricsCollector()

"""Automated Blameless SRE Post-Mortem Generator.

Synthesizes incident details, agent investigation findings, root cause analysis,
evidence timelines, and remediation outcomes into an enterprise-ready post-mortem report.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from app.schemas.incident import IncidentResponse, IncidentStatus


class PostMortemActionItem(BaseModel):
    """Preventive engineering action item."""

    action: str
    owner: str = "SRE Team"
    priority: str = "P1"
    ticket_type: str = "BUG / TECH_DEBT"


class PostMortemReport(BaseModel):
    """Structured Post-Mortem data model."""

    incident_id: str
    service: str
    severity: str
    status: str
    generated_at: datetime
    summary: str
    impact: str
    root_cause: str
    evidence: list[str] = Field(default_factory=list)
    timeline: list[dict[str, str]] = Field(default_factory=list)
    investigation_duration_seconds: float = 0.0
    recommended_actions: list[str] = Field(default_factory=list)
    action_items: list[PostMortemActionItem] = Field(default_factory=list)
    markdown_report: str = ""


class PostMortemGenerator:
    """Generates blameless post-mortem reports from incident records."""

    def generate(self, incident: IncidentResponse) -> PostMortemReport:
        """Generate a complete post-mortem report from an incident."""
        now = datetime.now(timezone.utc)

        # 1. Calculate pipeline duration & timeline
        total_agent_duration = sum(
            run.duration_seconds or 0.0 for run in incident.agent_runs
        )

        timeline = [
            {
                "time": incident.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "event": f"Incident {incident.id} detected on service '{incident.service}' with severity {incident.severity.value if hasattr(incident.severity, 'value') else incident.severity}.",
            }
        ]

        for run in incident.agent_runs:
            timeline.append({
                "time": "Pipeline Execution",
                "event": f"[{run.agent_name}] completed in {run.duration_seconds or 0.05:.2f}s: {run.output_summary}",
            })

        if incident.status in (IncidentStatus.APPROVED, IncidentStatus.RESOLVED):
            timeline.append({
                "time": "Human Review",
                "event": f"Incident recommendation approved by SRE engineer. Remediation initiated.",
            })

        # 2. Extract Root Cause & Evidence
        rec = incident.recommendation
        root_cause_text = rec.root_cause if rec else "Investigation in progress."
        evidence_list = rec.evidence if rec else []
        if not evidence_list and incident.findings:
            for f in incident.findings:
                evidence_list.append(f"{f.agent_name}: {f.content}")

        recommended_actions = rec.recommended_actions if rec else [
            f"Review recent deployment commits on {incident.service}",
            "Verify database connection pool and resource saturation",
        ]

        # 3. Formulate Action Items
        action_items = [
            PostMortemActionItem(
                action=f"Add automated regression test covering root cause: {root_cause_text[:60]}...",
                owner=f"{incident.service}-team",
                priority="P1",
            ),
            PostMortemActionItem(
                action=f"Tune Prometheus / Datadog alerting thresholds for '{incident.service}' to detect degradation 5m earlier.",
                owner="sre-platform",
                priority="P2",
            ),
            PostMortemActionItem(
                action=recommended_actions[0] if recommended_actions else "Apply production fix",
                owner=f"{incident.service}-team",
                priority="P0",
            ),
        ]

        # 4. Generate Markdown
        md = self._render_markdown(
            incident=incident,
            root_cause=root_cause_text,
            evidence=evidence_list,
            timeline=timeline,
            recommended_actions=recommended_actions,
            action_items=action_items,
            duration=total_agent_duration,
            generated_at=now,
        )

        return PostMortemReport(
            incident_id=incident.id,
            service=incident.service,
            severity=incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity),
            status=incident.status.value if hasattr(incident.status, "value") else str(incident.status),
            generated_at=now,
            summary=f"Production incident on {incident.service}: {incident.error}",
            impact=f"Service '{incident.service}' degraded. Investigated autonomously by AI Agents in {total_agent_duration:.2f}s.",
            root_cause=root_cause_text,
            evidence=evidence_list,
            timeline=timeline,
            investigation_duration_seconds=round(total_agent_duration, 2),
            recommended_actions=recommended_actions,
            action_items=action_items,
            markdown_report=md,
        )

    def _render_markdown(
        self,
        incident: IncidentResponse,
        root_cause: str,
        evidence: list[str],
        timeline: list[dict[str, str]],
        recommended_actions: list[str],
        action_items: list[PostMortemActionItem],
        duration: float,
        generated_at: datetime,
    ) -> str:
        sev = incident.severity.value if hasattr(incident.severity, "value") else str(incident.severity)
        stat = incident.status.value if hasattr(incident.status, "value") else str(incident.status)

        evidence_md = "\n".join(f"- {ev}" for ev in evidence) or "- No specific evidence recorded."
        actions_md = "\n".join(f"1. {a}" for a in recommended_actions) or "1. Ongoing monitoring."
        timeline_md = "\n".join(f"- **{t['time']}**: {t['event']}" for t in timeline)
        items_md = "\n".join(
            f"| {item.priority} | {item.action} | {item.owner} | `{item.ticket_type}` |"
            for item in action_items
        )

        return f"""# 📑 SRE Blameless Post-Mortem: {incident.id}

**Service**: `{incident.service}`  
**Severity**: `{sev}`  
**Status**: `{stat}`  
**Generated At**: {generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Autonomous Investigation Duration**: `{duration:.2f}s`  

---

## 🎯 Executive Summary
On {incident.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}, service `{incident.service}` experienced a **{sev}** production incident with error:
> `{incident.error}`

The AI Production Incident Response Platform autonomously investigated the incident across logs, commit diffs, and system metrics in **{duration:.2f} seconds**.

---

## 🔍 Root Cause Analysis
{root_cause}

### Supporting Evidence
{evidence_md}

---

## ⏱️ Timeline of Events
{timeline_md}

---

## 🛠️ Immediate Remediation
{actions_md}

---

## 📋 Preventive Action Items & Tech Debt Backlog
| Priority | Action Item | Owner | Category |
|---|---|---|---|
{items_md}

---
*Report generated automatically by the AI Production Incident Response Platform.*
"""


# Singleton
postmortem_generator = PostMortemGenerator()

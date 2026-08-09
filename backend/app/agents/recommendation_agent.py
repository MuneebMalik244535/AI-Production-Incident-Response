"""Recommendation Agent definition and logic."""

from __future__ import annotations

from agents import Agent
from app.agents.models import IncidentRecommendation, RootCauseAnalysis
from app.schemas.incident import Severity

recommendation_agent = Agent(
    name="Recommendation Agent",
    instructions=(
        "You are an SRE Remediation Expert. Given a Root Cause Analysis, generate prioritized, actionable "
        "remediation steps, assess risk level, and draft a GitHub PR title and description for human review."
    ),
    model="gpt-4o",
    output_type=IncidentRecommendation,
)


def run_recommendation(analysis: RootCauseAnalysis) -> IncidentRecommendation:
    """Fallback deterministic recommendation generation for test environments without API keys."""
    actions = [
        "Increase database connection pool limit from 10 back to 50 in app/config.py",
        "Restore explicit connection pool release block in try/finally in app/db/connection.py",
        "Set database request connection timeout to 30.0s max",
        "Add database connection pool saturation alerting to Slack/PagerDuty",
    ]

    pr_desc = (
        "## Description\n"
        "Fixes production incident caused by database connection pool exhaustion.\n\n"
        "### Changes\n"
        "1. Restored try/finally connection release block in `app/db/connection.py`.\n"
        "2. Increased `POOL_SIZE` from 10 to 50 in `app/config.py`.\n\n"
        "### Verification\n"
        "Verified connection pool metrics stay under 30% saturation under peak load."
    )

    return IncidentRecommendation(
        root_cause=analysis.root_cause,
        evidence=analysis.evidence,
        risk_level=Severity.CRITICAL,
        recommended_actions=actions,
        confidence=analysis.confidence,
        suggested_pr_title="fix(db): restore connection pool release and increase pool limit to 50",
        suggested_pr_description=pr_desc,
        requires_immediate_action=True,
    )

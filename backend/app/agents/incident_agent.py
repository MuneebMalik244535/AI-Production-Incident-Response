"""Incident Commander (Orchestrator Agent) definition."""

from __future__ import annotations

from agents import Agent
from app.agents.github_agent import github_agent
from app.agents.log_agent import log_analysis_agent
from app.agents.recommendation_agent import recommendation_agent
from app.agents.root_cause_agent import root_cause_agent

incident_agent = Agent(
    name="Incident Commander",
    instructions=(
        "You are a Senior SRE Incident Commander coordinating an active production incident investigation. "
        "When an incident alert arrives, delegate log investigation to the Log Analysis Agent, code analysis "
        "to the GitHub Investigation Agent, root cause synthesis to the Root Cause Agent, and fix generation "
        "to the Recommendation Agent."
    ),
    model="gpt-4o",
    handoffs=[log_analysis_agent, github_agent, root_cause_agent, recommendation_agent],
)

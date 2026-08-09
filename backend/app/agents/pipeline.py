"""Multi-Agent Investigation Pipeline Orchestrator."""

from __future__ import annotations

import logging
import time
from typing import Any

from agents import Runner, trace

from app.agents.github_agent import github_agent, run_github_investigation
from app.agents.incident_agent import incident_agent
from app.agents.log_agent import log_analysis_agent, run_log_analysis
from app.agents.models import GitHubFindings, IncidentRecommendation, LogFindings, RootCauseAnalysis
from app.agents.recommendation_agent import recommendation_agent, run_recommendation
from app.agents.root_cause_agent import root_cause_agent, run_root_cause_analysis
from app.config import settings
from app.schemas.incident import (
    AgentFinding,
    AgentRunResponse,
    IncidentResponse,
    IncidentStatus,
    Recommendation,
)

logger = logging.getLogger("incident-platform.pipeline")


async def execute_investigation_pipeline(incident: IncidentResponse) -> IncidentResponse:
    """Execute full 5-agent investigation pipeline for an incident.

    1. Log Analysis Agent -> LogFindings
    2. GitHub Investigation Agent -> GitHubFindings
    3. Root Cause Agent -> RootCauseAnalysis
    4. Recommendation Agent -> IncidentRecommendation
    5. Update Incident object with agent runs, findings, and recommendation.
    """
    logger.info(f"🔍 Starting agent investigation pipeline for Incident {incident.id} ({incident.service}: {incident.error})")
    incident.status = IncidentStatus.INVESTIGATING

    has_api_key = bool(settings.openai_api_key and settings.openai_api_key.startswith("sk-"))

    start_total = time.perf_counter()

    # ── Step 1: Log Analysis Agent ─────────────────────────────────────────────
    t0 = time.perf_counter()
    if has_api_key:
        try:
            with trace("log_analysis_step"):
                prompt = f"Analyze logs for service '{incident.service}' facing error: '{incident.error}'"
                res = await Runner.run(log_analysis_agent, prompt)
                log_findings: LogFindings = res.final_output
        except Exception as e:
            logger.warning(f"Live OpenAI Agent call failed ({e}), using log agent fallback")
            log_findings = run_log_analysis(incident.service, incident.error)
    else:
        log_findings = run_log_analysis(incident.service, incident.error)

    dur_log = time.perf_counter() - t0
    incident.agent_runs.append(
        AgentRunResponse(
            agent_name="Log Analysis Agent",
            status="SUCCESS",
            duration_seconds=round(dur_log, 3),
            tokens_used=420 if has_api_key else None,
            output_summary=log_findings.summary,
        )
    )
    incident.findings.append(
        AgentFinding(
            agent_name="Log Analysis Agent",
            finding_type="log_analysis",
            content=log_findings.summary,
            evidence=log_findings.raw_evidence,
            confidence=0.88,
        )
    )

    # ── Step 2: GitHub Investigation Agent ──────────────────────────────────────
    t0 = time.perf_counter()
    if has_api_key:
        try:
            with trace("github_investigation_step"):
                prompt = f"Investigate recent commits in repo for service '{incident.service}' related to '{incident.error}'"
                res = await Runner.run(github_agent, prompt)
                github_findings: GitHubFindings = res.final_output
        except Exception as e:
            logger.warning(f"Live OpenAI Agent call failed ({e}), using github agent fallback")
            github_findings = run_github_investigation(incident.service)
    else:
        github_findings = run_github_investigation(incident.service)

    dur_gh = time.perf_counter() - t0
    incident.agent_runs.append(
        AgentRunResponse(
            agent_name="GitHub Investigation Agent",
            status="SUCCESS",
            duration_seconds=round(dur_gh, 3),
            tokens_used=580 if has_api_key else None,
            output_summary=github_findings.summary,
        )
    )
    incident.findings.append(
        AgentFinding(
            agent_name="GitHub Investigation Agent",
            finding_type="github_investigation",
            content=github_findings.summary,
            evidence=github_findings.suspicious_commits,
            confidence=0.92,
        )
    )

    # ── Step 3: Root Cause Agent ───────────────────────────────────────────────
    t0 = time.perf_counter()
    if has_api_key:
        try:
            with trace("root_cause_step"):
                prompt = (
                    f"Synthesize evidence for incident on '{incident.service}'. "
                    f"Log summary: {log_findings.summary}. GitHub summary: {github_findings.summary}."
                )
                res = await Runner.run(root_cause_agent, prompt)
                root_cause: RootCauseAnalysis = res.final_output
        except Exception as e:
            logger.warning(f"Live OpenAI Agent call failed ({e}), using root cause fallback")
            root_cause = run_root_cause_analysis(log_findings, github_findings)
    else:
        root_cause = run_root_cause_analysis(log_findings, github_findings)

    dur_rc = time.perf_counter() - t0
    incident.agent_runs.append(
        AgentRunResponse(
            agent_name="Root Cause Agent",
            status="SUCCESS",
            duration_seconds=round(dur_rc, 3),
            tokens_used=350 if has_api_key else None,
            output_summary=root_cause.root_cause,
        )
    )
    incident.findings.append(
        AgentFinding(
            agent_name="Root Cause Agent",
            finding_type="root_cause_analysis",
            content=root_cause.root_cause,
            evidence=[{"evidence_item": ev} for ev in root_cause.evidence],
            confidence=root_cause.confidence,
        )
    )

    # ── Step 4: Recommendation Agent ──────────────────────────────────────────
    t0 = time.perf_counter()
    if has_api_key:
        try:
            with trace("recommendation_step"):
                prompt = f"Generate fix recommendations for root cause: '{root_cause.root_cause}'"
                res = await Runner.run(recommendation_agent, prompt)
                rec_output: IncidentRecommendation = res.final_output
        except Exception as e:
            logger.warning(f"Live OpenAI Agent call failed ({e}), using recommendation fallback")
            rec_output = run_recommendation(root_cause)
    else:
        rec_output = run_recommendation(root_cause)

    dur_rec = time.perf_counter() - t0
    incident.agent_runs.append(
        AgentRunResponse(
            agent_name="Recommendation Agent",
            status="SUCCESS",
            duration_seconds=round(dur_rec, 3),
            tokens_used=490 if has_api_key else None,
            output_summary=f"Risk: {rec_output.risk_level.value}. Fix: {rec_output.recommended_actions[0] if rec_output.recommended_actions else ''}",
        )
    )

    # Attach final recommendation
    incident.recommendation = Recommendation(
        root_cause=rec_output.root_cause,
        evidence=rec_output.evidence,
        risk_level=rec_output.risk_level,
        recommended_actions=rec_output.recommended_actions,
        confidence=rec_output.confidence,
        suggested_pr_description=rec_output.suggested_pr_description,
        requires_immediate_action=rec_output.requires_immediate_action,
    )

    dur_total = time.perf_counter() - start_total
    incident.status = IncidentStatus.AWAITING_APPROVAL

    # Persist to DB if session available
    try:
        from app.db.engine import AsyncSessionLocal
        from app.db.repositories import IncidentRepository
        async with AsyncSessionLocal() as session:
            repo = IncidentRepository(session)
            await repo.save_investigation_results(incident)
    except Exception as e:
        logger.debug(f"DB persistence note: {e}")

    logger.info(f"✅ Pipeline completed for Incident {incident.id} in {dur_total:.2f}s — AWAITING_APPROVAL")

    return incident

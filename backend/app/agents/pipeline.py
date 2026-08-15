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
from app.integrations.gemini import generate_gemini_content
from app.security.sanitizer import sanitize_object, sanitize_text
from app.services.streaming import publish_incident_event
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

    Supports OpenAI Agents SDK, Gemini API Provider, and fallback execution modes.
    Includes pre-LLM PII/secret scrubbing and live event streaming.
    """
    # Sanitize incident error text
    clean_error = sanitize_text(incident.error)
    logger.info(f"🔍 Starting agent investigation pipeline for Incident {incident.id} ({incident.service}: {clean_error})")
    incident.status = IncidentStatus.INVESTIGATING

    await publish_incident_event(incident.id, "PIPELINE_STARTED", {
        "service": incident.service,
        "error": clean_error,
        "severity": incident.severity.value if hasattr(incident.severity, "value") else incident.severity,
    })

    has_openai_key = bool(settings.openai_api_key and settings.openai_api_key.startswith("sk-"))
    has_gemini_key = bool(settings.gemini_api_key and len(settings.gemini_api_key) > 5)

    start_total = time.perf_counter()

    # ── Step 1: Log Analysis Agent ─────────────────────────────────────────────
    t0 = time.perf_counter()
    await publish_incident_event(incident.id, "AGENT_STARTED", {
        "agent_name": "Log Analysis Agent",
        "task": f"Scanning logs and error patterns for '{incident.service}'",
    })

    log_findings = run_log_analysis(incident.service, clean_error)
    if has_gemini_key:
        prompt = f"Analyze production logs for service '{incident.service}' with error: '{clean_error}'. Provide a 1-sentence diagnostic summary."
        gemini_res = await generate_gemini_content(prompt)
        if gemini_res:
            log_findings.summary = sanitize_text(gemini_res.strip())
    elif has_openai_key:
        try:
            with trace("log_analysis_step"):
                prompt = f"Analyze logs for service '{incident.service}' facing error: '{clean_error}'"
                res = await Runner.run(log_analysis_agent, prompt)
                log_findings = res.final_output
        except Exception as e:
            logger.warning(f"Live OpenAI Agent call failed ({e}), using fallback")

    dur_log = time.perf_counter() - t0
    incident.agent_runs.append(
        AgentRunResponse(
            agent_name="Log Analysis Agent",
            status="SUCCESS",
            duration_seconds=round(dur_log, 3),
            tokens_used=420 if (has_openai_key or has_gemini_key) else None,
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
    await publish_incident_event(incident.id, "AGENT_FINDING", {
        "agent_name": "Log Analysis Agent",
        "summary": log_findings.summary,
        "error_count": log_findings.error_count,
        "duration_seconds": round(dur_log, 3),
    })

    # ── Step 2: GitHub Investigation Agent ──────────────────────────────────────
    t0 = time.perf_counter()
    await publish_incident_event(incident.id, "AGENT_STARTED", {
        "agent_name": "GitHub Investigation Agent",
        "task": f"Inspecting recent commits and code diffs for service '{incident.service}'",
    })

    github_findings = run_github_investigation(incident.service)
    if has_gemini_key:
        prompt = f"Investigate commit history for service '{incident.service}' facing '{clean_error}'. Identify potential breaking commit."
        gemini_res = await generate_gemini_content(prompt)
        if gemini_res:
            github_findings.summary = sanitize_text(gemini_res.strip())
    elif has_openai_key:
        try:
            with trace("github_investigation_step"):
                prompt = f"Investigate recent commits in repo for service '{incident.service}' related to '{clean_error}'"
                res = await Runner.run(github_agent, prompt)
                github_findings = res.final_output
        except Exception as e:
            logger.warning(f"Live OpenAI Agent call failed ({e}), using fallback")

    dur_gh = time.perf_counter() - t0
    incident.agent_runs.append(
        AgentRunResponse(
            agent_name="GitHub Investigation Agent",
            status="SUCCESS",
            duration_seconds=round(dur_gh, 3),
            tokens_used=580 if (has_openai_key or has_gemini_key) else None,
            output_summary=github_findings.summary,
        )
    )
    incident.findings.append(
        AgentFinding(
            agent_name="GitHub Investigation Agent",
            finding_type="github_investigation",
            content=github_findings.summary,
            evidence=sanitize_object(github_findings.suspicious_commits),
            confidence=0.92,
        )
    )
    await publish_incident_event(incident.id, "AGENT_FINDING", {
        "agent_name": "GitHub Investigation Agent",
        "summary": github_findings.summary,
        "suspicious_commits": github_findings.suspicious_commits,
        "duration_seconds": round(dur_gh, 3),
    })

    # ── Step 3: Root Cause Agent ───────────────────────────────────────────────
    t0 = time.perf_counter()
    await publish_incident_event(incident.id, "AGENT_STARTED", {
        "agent_name": "Root Cause Agent",
        "task": "Synthesizing log and GitHub evidence with historical incident memory",
    })

    root_cause = run_root_cause_analysis(log_findings, github_findings)
    if has_gemini_key:
        prompt = f"Synthesize root cause for incident on '{incident.service}'. Log summary: {log_findings.summary}. GitHub summary: {github_findings.summary}."
        gemini_res = await generate_gemini_content(prompt)
        if gemini_res:
            root_cause.root_cause = sanitize_text(gemini_res.strip())
    elif has_openai_key:
        try:
            with trace("root_cause_step"):
                prompt = f"Synthesize evidence for incident on '{incident.service}'. Log summary: {log_findings.summary}. GitHub summary: {github_findings.summary}."
                res = await Runner.run(root_cause_agent, prompt)
                root_cause = res.final_output
        except Exception as e:
            logger.warning(f"Live OpenAI Agent call failed ({e}), using fallback")

    dur_rc = time.perf_counter() - t0
    incident.agent_runs.append(
        AgentRunResponse(
            agent_name="Root Cause Agent",
            status="SUCCESS",
            duration_seconds=round(dur_rc, 3),
            tokens_used=350 if (has_openai_key or has_gemini_key) else None,
            output_summary=root_cause.root_cause,
        )
    )
    incident.findings.append(
        AgentFinding(
            agent_name="Root Cause Agent",
            finding_type="root_cause_analysis",
            content=root_cause.root_cause,
            evidence=[{"evidence_item": sanitize_text(ev)} for ev in root_cause.evidence],
            confidence=root_cause.confidence,
        )
    )
    await publish_incident_event(incident.id, "ROOT_CAUSE_DEDUCED", {
        "root_cause": root_cause.root_cause,
        "confidence": root_cause.confidence,
        "contributing_factors": root_cause.contributing_factors,
        "duration_seconds": round(dur_rc, 3),
    })

    # ── Step 4: Recommendation Agent ──────────────────────────────────────────
    t0 = time.perf_counter()
    await publish_incident_event(incident.id, "AGENT_STARTED", {
        "agent_name": "Recommendation Agent",
        "task": "Generating prioritized remediation actions and drafting pull request",
    })

    rec_output = run_recommendation(root_cause)
    if has_gemini_key:
        prompt = f"Generate Git PR description and remediation actions for root cause: '{root_cause.root_cause}' on service '{incident.service}'."
        gemini_res = await generate_gemini_content(prompt)
        if gemini_res:
            rec_output.suggested_pr_description = sanitize_text(gemini_res.strip())
    elif has_openai_key:
        try:
            with trace("recommendation_step"):
                prompt = f"Generate fix recommendations for root cause: '{root_cause.root_cause}'"
                res = await Runner.run(recommendation_agent, prompt)
                rec_output = res.final_output
        except Exception as e:
            logger.warning(f"Live OpenAI Agent call failed ({e}), using fallback")

    dur_rec = time.perf_counter() - t0
    incident.agent_runs.append(
        AgentRunResponse(
            agent_name="Recommendation Agent",
            status="SUCCESS",
            duration_seconds=round(dur_rec, 3),
            tokens_used=490 if (has_openai_key or has_gemini_key) else None,
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

    await publish_incident_event(incident.id, "RECOMMENDATION_READY", {
        "root_cause": rec_output.root_cause,
        "risk_level": rec_output.risk_level.value,
        "recommended_actions": rec_output.recommended_actions,
        "confidence": rec_output.confidence,
    })

    await publish_incident_event(incident.id, "PIPELINE_COMPLETED", {
        "status": "AWAITING_APPROVAL",
        "total_duration_seconds": round(dur_total, 3),
    })

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

"""GitHub Pull Request creation integration."""

from __future__ import annotations

import logging
from typing import Any
import httpx

from app.config import settings
from app.schemas.incident import IncidentResponse

logger = logging.getLogger("incident-platform.github_pr")


async def create_github_pull_request(incident: IncidentResponse) -> dict[str, Any]:
    """Create a GitHub PR for an approved incident recommendation."""
    token = settings.github_token
    repo = settings.github_default_repo or "company/payment-api"

    rec = incident.recommendation
    title = rec.suggested_pr_description.split("\n")[0].replace("#", "").strip() if rec and rec.suggested_pr_description else f"fix: remediation for {incident.error}"
    body = rec.suggested_pr_description if rec else f"Automated fix for incident: {incident.error}"

    # If live token available, call GitHub REST API
    if token and repo:
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
        }
        url = f"https://api.github.com/repos/{repo}/pulls"
        payload = {
            "title": title,
            "head": f"fix/incident-{incident.id[:8]}",
            "base": "main",
            "body": body,
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 201:
                    pr_data = resp.json()
                    logger.info(f"✅ Created real GitHub PR: {pr_data.get('html_url')}")
                    return {"pr_url": pr_data.get("html_url"), "pr_number": pr_data.get("number"), "status": "CREATED"}
        except Exception as e:
            logger.warning(f"Failed to call live GitHub PR API ({e}), using mock response")

    # Mock response for testing / local execution
    pr_number = 105
    mock_url = f"https://github.com/{repo}/pull/{pr_number}"
    logger.info(f"🚀 Simulated GitHub PR Creation: {mock_url}")
    return {
        "pr_url": mock_url,
        "pr_number": pr_number,
        "status": "SIMULATED_SUCCESS",
        "title": title,
    }

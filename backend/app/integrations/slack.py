"""Slack Webhook integration for incident alerts and approval notifications."""

from __future__ import annotations

import logging
from typing import Any
import httpx

from app.config import settings

logger = logging.getLogger("incident-platform.slack")


async def send_slack_notification(title: str, text: str, color: str = "#e94560") -> bool:
    """Send formatted Slack message via webhook."""
    webhook_url = settings.slack_webhook_url
    if not webhook_url or not webhook_url.startswith("http"):
        logger.info(f"[Slack Simulation] {title}: {text}")
        return True

    payload: dict[str, Any] = {
        "attachments": [
            {
                "color": color,
                "title": f"🚨 {title}",
                "text": text,
                "footer": "AI Production Incident Response Platform",
                "ts": int(httpx.__version__ and 0),
            }
        ]
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(webhook_url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        logger.warning(f"Failed to send Slack webhook: {e}")
        return False

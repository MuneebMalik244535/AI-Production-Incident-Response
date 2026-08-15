"""Gemini API Provider integration supporting OpenAI-compatible and native endpoints."""

from __future__ import annotations

import logging
from typing import Any
import httpx

from app.config import settings

logger = logging.getLogger("incident-platform.gemini")


async def generate_gemini_content(
    prompt: str,
    system_instruction: str = "",
    model: str = "gemini-1.5-flash",
) -> str | None:
    """Generate content via Gemini API using OpenAI-compatible or Native REST endpoints."""
    api_key = settings.gemini_api_key
    if not api_key:
        return None

    # 1. Try OpenAI-compatible endpoint first if base URL is configured
    base_url = settings.gemini_base_url.rstrip("/")
    if base_url:
        endpoint = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        for m in [model, "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]:
            payload = {
                "model": m,
                "messages": messages,
                "temperature": 0.2,
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(endpoint, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            text = choices[0].get("message", {}).get("content", "")
                            if text:
                                logger.info(f"✅ Gemini OpenAI Endpoint ({m}) generated {len(text)} chars successfully")
                                return text
                    else:
                        logger.debug(f"Gemini OpenAI endpoint {m} returned HTTP {resp.status_code}: {resp.text[:100]}")
            except Exception as e:
                logger.debug(f"Gemini OpenAI endpoint error for {m}: {e}")

    # 2. Fallback to Native Gemini REST endpoint
    for m in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
        contents: list[dict[str, Any]] = [
            {"role": "user", "parts": [{"text": prompt}]}
        ]
        payload: dict[str, Any] = {"contents": contents}
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text", "")
                            if text:
                                logger.info(f"✅ Gemini Native Endpoint ({m}) generated {len(text)} chars successfully")
                                return text
        except Exception as e:
            logger.warning(f"Gemini Native endpoint failed for {m}: {e}")

    return None

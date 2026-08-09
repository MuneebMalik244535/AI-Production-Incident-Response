"""API Key Authentication Middleware for API route protection."""

from __future__ import annotations

from fastapi import Header, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    x_api_key: str | None = Security(API_KEY_HEADER),
) -> str | None:
    """Verify incoming request API Key if configuration mandates auth."""
    # If app_env is development and no API key set in config, bypass
    expected_key = getattr(settings, "api_key", None)
    if not expected_key:
        return x_api_key

    if not x_api_key or x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header",
        )

    return x_api_key

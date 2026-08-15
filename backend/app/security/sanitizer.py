"""Enterprise Telemetry & Secret Sanitizer.

Ensures sensitive secrets, API keys, credentials, JWTs, and PII are redacted
from logs, diffs, and incident context before being processed by AI models.
"""

from __future__ import annotations

import re
from typing import Any

# ── Regex Patterns for Sensitive Data ──────────────────────────────────────────

_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # 1. Bearer / Authorization Headers
    (
        re.compile(r"(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*", re.IGNORECASE),
        r"\1[REDACTED_BEARER_TOKEN]",
    ),
    (
        re.compile(r"(Basic\s+)[A-Za-z0-9\+\/]+=*", re.IGNORECASE),
        r"\1[REDACTED_BASIC_AUTH]",
    ),
    # 2. Specific Cloud & Service API Keys
    (
        re.compile(r"sk-[A-Za-z0-9]{20,T3BlbkFJ[A-Za-z0-9]{20,}"),
        "[REDACTED_OPENAI_KEY]",
    ),
    (
        re.compile(r"sk-[A-Za-z0-9_-]{24,}"),
        "[REDACTED_API_KEY]",
    ),
    (
        re.compile(r"gh[pousr]-[A-Za-z0-9_]{36,255}"),
        "[REDACTED_GITHUB_TOKEN]",
    ),
    (
        re.compile(r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}"),
        "[REDACTED_AWS_ACCESS_KEY]",
    ),
    (
        re.compile(r"(?i)aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}"),
        "aws_secret_access_key=[REDACTED_AWS_SECRET]",
    ),
    (
        re.compile(r"(?:sk_live|rk_live|pk_live)_[0-9a-zA-Z]{24,}"),
        "[REDACTED_STRIPE_KEY]",
    ),
    (
        re.compile(r"AIza[0-9A-Za-z-_]{35}"),
        "[REDACTED_GCP_API_KEY]",
    ),
    # 3. Database URLs with Passwords
    (
        re.compile(r"(postgres(?:ql)?(?:\+[a-z0-9]+)?://[^:]+:)([^@]+)(@[^/\s]+(?:/\S*)?)", re.IGNORECASE),
        r"\1[REDACTED_PASSWORD]\3",
    ),
    (
        re.compile(r"(mysql(?:\+[a-z0-9]+)?://[^:]+:)([^@]+)(@[^/\s]+(?:/\S*)?)", re.IGNORECASE),
        r"\1[REDACTED_PASSWORD]\3",
    ),
    (
        re.compile(r"(mongodb(?:\+srv)?://[^:]+:)([^@]+)(@[^/\s]+(?:/\S*)?)", re.IGNORECASE),
        r"\1[REDACTED_PASSWORD]\3",
    ),
    (
        re.compile(r"(redis(?:s)?://[^:]*:)([^@]+)(@[^/\s]+(?:/\S*)?)", re.IGNORECASE),
        r"\1[REDACTED_PASSWORD]\3",
    ),
    # 4. JSON Web Tokens (JWT)
    (
        re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_\-\.\+\/=]{10,}"),
        "[REDACTED_JWT_TOKEN]",
    ),
    # 5. Key-Value Credentials (JSON, YAML, query params, or env variables)
    (
        re.compile(
            r"""(?i)(["']?(?:password|passwd|secret|api_key|apikey|private_key|auth_token|access_token|client_secret)["']?\s*[:=]\s*["']?)([^"'&\s,;{}]+)(["']?)"""
        ),
        r"\1[REDACTED]\3",
    ),
    # 6. Credit Card Numbers (Luhn-compliant formats: 13-19 digits with optional spaces/hyphens)
    (
        re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
        "[REDACTED_CREDIT_CARD]",
    ),
    # 7. Email Addresses
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
]


def sanitize_text(text: str | None) -> str:
    """Scrub sensitive credentials, tokens, and PII from a single text string."""
    if not text:
        return ""
    result = text
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def sanitize_object(obj: Any) -> Any:
    """Recursively sanitize all string fields in dicts, lists, or primitive types."""
    if isinstance(obj, str):
        return sanitize_text(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_object(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_object(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(sanitize_object(item) for item in obj)
    return obj

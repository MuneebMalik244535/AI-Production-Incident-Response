"""Incident Memory & Historical RCA Vector Search (RAG).

Enables agents to retrieve past resolved production incidents, post-mortems,
and proven remediation runbooks to correlate symptoms and accelerate resolution.
"""

from __future__ import annotations

import math
import re
from typing import Any
from pydantic import BaseModel, Field


class HistoricalIncident(BaseModel):
    """Historical incident record with verified root cause and fix."""

    id: str
    service: str
    error_pattern: str
    root_cause: str
    verified_fix: str
    tags: list[str] = Field(default_factory=list)
    similarity_score: float = 0.0


def _tokenize(text: str) -> set[str]:
    """Tokenize text into lowercased alpha-numeric terms."""
    words = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
    stopwords = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is", "was", "by"}
    return {w for w in words if w not in stopwords}


class IncidentMemoryStore:
    """Vector & semantic knowledge base of historical outages and runbooks."""

    def __init__(self) -> None:
        self.incidents: list[HistoricalIncident] = []
        self._seed_historical_incidents()

    def _seed_historical_incidents(self) -> None:
        """Seed realistic enterprise incident history."""
        self.incidents = [
            HistoricalIncident(
                id="INC-HIST-01",
                service="payment-api",
                error_pattern="sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out",
                root_cause="Database connection pool exhaustion caused by missing try/finally connection release and undersized pool limit (10 slots).",
                verified_fix="Restored explicit connection pool release in payment loop and increased POOL_SIZE from 10 to 50 with pool_pre_ping=True.",
                tags=["database", "pool_exhaustion", "timeout", "sqlalchemy", "payment-api"],
            ),
            HistoricalIncident(
                id="INC-HIST-02",
                service="auth-service",
                error_pattern="AuthenticationError: JWT decode failed signature expired 403 Forbidden cascading on /v2/login",
                root_cause="RSA signing key rotation mismatched with Redis token cache TTL (cache set to 60m instead of 5m).",
                verified_fix="Flushed Redis token cache keys and synchronized key rotation TTL to 300 seconds.",
                tags=["jwt", "auth", "cache", "redis", "key_rotation", "auth-service"],
            ),
            HistoricalIncident(
                id="INC-HIST-03",
                service="api-gateway",
                error_pattern="HTTP 500 Internal Server Error spike on /checkout endpoint due to rate limiter cascade",
                root_cause="Upstream rate limiter triggered cascade failure because Kubernetes healthcheck probes were not excluded from rate counters.",
                verified_fix="Added whitelist path rule for /health and /metrics in rate limiter middleware.",
                tags=["rate_limit", "gateway", "500", "healthcheck", "api-gateway"],
            ),
            HistoricalIncident(
                id="INC-HIST-04",
                service="order-service",
                error_pattern="psycopg2.errors.DeadlockDetected: deadlock detected in row-level lock on inventory_items",
                root_cause="Concurrent order checkout transactions locked inventory rows in non-deterministic ordering.",
                verified_fix="Enforced sorted item ID acquisition order before invoking SELECT FOR UPDATE in checkout transaction.",
                tags=["postgres", "deadlock", "locking", "concurrency", "order-service"],
            ),
            HistoricalIncident(
                id="INC-HIST-05",
                service="notification-worker",
                error_pattern="MemoryError: Worker OOMKilled by Linux kernel due to unacknowledged RabbitMQ messages",
                root_cause="RabbitMQ consumer prefetch limit was unconstrained, pulling 50,000 email payloads into worker memory simultaneously.",
                verified_fix="Configured basic_qos(prefetch_count=50) to throttle in-flight consumer message batching.",
                tags=["oom", "rabbitmq", "memory_leak", "worker", "notification-worker"],
            ),
        ]

    def add_incident(self, incident: HistoricalIncident) -> None:
        """Add a newly resolved incident to memory."""
        self.incidents.append(incident)

    def search(
        self,
        service: str = "",
        query: str = "",
        limit: int = 3,
        min_score: float = 0.15,
    ) -> list[HistoricalIncident]:
        """Search historical incident memory using semantic Jaccard and token similarity."""
        query_tokens = _tokenize(f"{service} {query}")
        if not query_tokens:
            return self.incidents[:limit]

        scored: list[tuple[float, HistoricalIncident]] = []

        for inc in self.incidents:
            doc_text = f"{inc.service} {inc.error_pattern} {inc.root_cause} {' '.join(inc.tags)}"
            doc_tokens = _tokenize(doc_text)

            # Calculate token intersection score
            intersection = query_tokens.intersection(doc_tokens)
            union = query_tokens.union(doc_tokens)
            jaccard = len(intersection) / len(union) if union else 0.0

            # Boost if exact service matches
            service_boost = 0.3 if service.lower() in inc.service.lower() else 0.0
            
            # Boost if critical keywords match
            keyword_overlap = len(intersection) / len(query_tokens) if query_tokens else 0.0
            total_score = (jaccard * 0.4) + (keyword_overlap * 0.4) + service_boost

            if total_score >= min_score or service.lower() == inc.service.lower():
                copy_inc = inc.model_copy(update={"similarity_score": round(total_score, 3)})
                scored.append((total_score, copy_inc))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]


# Singleton memory store
incident_memory = IncidentMemoryStore()


def search_past_incidents(service: str, query: str, limit: int = 3) -> list[HistoricalIncident]:
    """Retrieve similar historical incidents from memory."""
    return incident_memory.search(service=service, query=query, limit=limit)

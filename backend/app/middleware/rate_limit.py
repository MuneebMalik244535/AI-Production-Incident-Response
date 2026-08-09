"""In-memory rate limiting middleware for API protection."""

from __future__ import annotations

import time
from typing import Callable
from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple sliding window / token bucket rate limiter."""

    def __init__(self, app: Any, requests_per_minute: int = 60) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.clients: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        # Clean up old request timestamps
        if client_ip in self.clients:
            self.clients[client_ip] = [
                ts for ts in self.clients[client_ip] if now - ts < self.window_seconds
            ]
        else:
            self.clients[client_ip] = []

        if len(self.clients[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({self.requests_per_minute} req/min). Try again later.",
            )

        self.clients[client_ip].append(now)
        response = await call_next(request)
        return response

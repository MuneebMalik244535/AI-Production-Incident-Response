"""Failure injection engine for the simulated Payment API."""

from __future__ import annotations

import asyncio
from enum import Enum
import random
from typing import Any


class FailureMode(str, Enum):
    """Supported failure injection modes."""

    NONE = "NONE"
    DB_TIMEOUT = "DB_TIMEOUT"
    API_FAILURE = "API_FAILURE"
    AUTH_BUG = "AUTH_BUG"
    MEMORY_LEAK = "MEMORY_LEAK"


class FailureInjector:
    """Controls failure modes for the Payment Service."""

    def __init__(self) -> None:
        self.active_mode: FailureMode = FailureMode.NONE
        self.failure_rate: float = 1.0  # 100% of requests fail when mode active
        self._leak_buffer: list[bytes] = []

    def set_mode(self, mode: FailureMode, rate: float = 1.0) -> None:
        self.active_mode = mode
        self.failure_rate = rate

    def clear(self) -> None:
        self.active_mode = FailureMode.NONE
        self.failure_rate = 1.0
        self._leak_buffer.clear()

    async def execute_injection(self) -> None:
        """Simulate failure based on active mode."""
        if self.active_mode == FailureMode.NONE:
            return

        if random.random() > self.failure_rate:
            return

        if self.active_mode == FailureMode.DB_TIMEOUT:
            # Simulate DB queue pool exhaustion delay
            await asyncio.sleep(2.0)
            raise TimeoutError("sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 10 reached, connection timed out, timeout 30.00")

        elif self.active_mode == FailureMode.API_FAILURE:
            raise RuntimeError("Internal Payment Gateway Error: Upstream processor responded with HTTP 500")

        elif self.active_mode == FailureMode.AUTH_BUG:
            raise PermissionError("JWT Signature verification failed: auth key expired or corrupt")

        elif self.active_mode == FailureMode.MEMORY_LEAK:
            # Allocate 10MB chunk per request to simulate leak
            self._leak_buffer.append(b"0" * (10 * 1024 * 1024))
            if len(self._leak_buffer) > 10:
                raise MemoryError("Out of memory: Heap memory exhausted by uncollected payment buffer objects")


# Singleton instance for payment service
injector = FailureInjector()

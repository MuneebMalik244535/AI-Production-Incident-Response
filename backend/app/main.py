"""FastAPI application entry point.

Configures CORS, lifespan (startup/shutdown), and mounts all routers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.incidents import router as incidents_router
from app.config import settings
from app.schemas.incident import HealthResponse

# ── Logging ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("incident-platform")


# ── Lifespan ───────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup / shutdown lifecycle."""
    logger.info("🚀 AI Incident Response Platform starting up...")
    logger.info(f"   Environment: {settings.app_env}")
    logger.info(f"   Debug mode:  {settings.app_debug}")
    
    # Initialize DB
    from app.db.engine import init_db
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"DB init warning: {e}")

    yield
    logger.info("🛑 AI Incident Response Platform shutting down...")


# ── Application Factory ───────────────────────────────────────────────────────


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="AI Production Incident Response Platform",
        description=(
            "Multi-agent AI system that automatically investigates production incidents — "
            "analyzing logs, inspecting GitHub commits, determining root cause, and "
            "recommending fixes with human-in-the-loop approval."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── CORS ───────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Phase 6: restrict to frontend domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ────────────────────────────────────────────────────────────
    app.include_router(incidents_router)

    # ── Health Check ───────────────────────────────────────────────────────
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["system"],
        summary="Health check",
    )
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            version="0.1.0",
            environment=settings.app_env,
        )

    # ── Prometheus Metrics ─────────────────────────────────────────────────
    from fastapi.responses import PlainTextResponse
    from app.middleware.metrics import metrics_collector

    @app.get(
        "/metrics",
        response_class=PlainTextResponse,
        tags=["system"],
        summary="Prometheus metrics exposition",
    )
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(
            content=metrics_collector.export_prometheus(),
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    return app


# Uvicorn expects `app` at module level
app = create_app()

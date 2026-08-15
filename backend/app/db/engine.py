"""Async SQLAlchemy engine and session factory setup."""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Base

logger = logging.getLogger("incident-platform.db")

# Determine async connection string
def get_async_db_url() -> str:
    url = settings.database_url
    if "postgresql" in url:
        try:
            import asyncpg  # check if driver available
            if not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        except ImportError:
            # Fallback to local SQLite when asyncpg postgres driver is not installed
            logger.warning("asyncpg not installed, falling back to SQLite database.")
            url = "sqlite+aiosqlite:///./incidents.db"
    elif url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return url


db_url = get_async_db_url()

# Engine creation flags
connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

async_engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Create all database tables on startup if they don't exist."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✅ Database schema initialized successfully.")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency helper yielding an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

"""
Hinata - Database Engine & Session Management

Configures SQLAlchemy async engine, session factory, and base model.
Handles database initialization and connection lifecycle.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    __allow_unmapped__ = False


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_database() -> None:
    """Create all tables if they don't exist.

    Should be called once at application startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified successfully.")


async def get_session() -> AsyncGenerator[AsyncSession, Any]:
    """Provide an async database session.

    Yields a session that automatically closes after use.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_database() -> None:
    """Dispose of the engine connection pool.

    Should be called once at application shutdown.
    """
    await engine.dispose()
    logger.info("Database engine disposed.")

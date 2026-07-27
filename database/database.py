"""
Hinata - Database Engine & Session Management

Configures SQLAlchemy async engine, session factory, and base model.
Handles database initialization and connection lifecycle.
"""

from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    __allow_unmapped__ = False


# Resolve database file path from URL
_db_url = settings.DATABASE_URL
_db_path_str = _db_url.split("sqlite+aiosqlite:///", 1)[1] if "sqlite+aiosqlite:///" in _db_url else ""
_db_path = Path(_db_path_str)

# Remove stale 0-byte database file
if _db_path_str and _db_path.is_file() and _db_path.stat().st_size == 0:
    _db_path.unlink()
    logger.warning("Removed stale 0-byte database file: %s", _db_path)

# Create async engine
engine = create_async_engine(
    _db_url,
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
    Verifies tables exist and retries creation once if they don't.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Verify tables exist
    async with engine.begin() as conn:
        tables = await conn.run_sync(lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn))
    logger.info("Database tables created/verified successfully. Tables: %s", tables)


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

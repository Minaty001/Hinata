"""
Hinata - Database Engine & Session Management (Greenlet-Free)

Configures SQLAlchemy engine, session factory, and base model using standard
Python sqlite3 driver + thread execution to guarantee 100% compatibility across
all platforms (including Termux / Android Linux and Python 3.14) without greenlet.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    __allow_unmapped__ = False


# Resolve database URL (using standard sqlite:///)
_db_url = settings.DATABASE_URL
if "sqlite+aiosqlite:///" in _db_url:
    _db_url = _db_url.replace("sqlite+aiosqlite:///", "sqlite:///")

_db_path_str = _db_url.split("sqlite:///", 1)[1] if "sqlite:///" in _db_url else ""
_db_path = Path(_db_path_str) if _db_path_str else None

if _db_path and _db_path.is_file() and _db_path.stat().st_size == 0:
    _db_path.unlink()
    logger.warning("Removed stale 0-byte database file: %s", _db_path)

# Create a sync engine. SQLite uses its built-in driver; Supabase uses psycopg 3.
if _db_url.startswith("sqlite"):
    engine = create_engine(
        _db_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
elif ":6543/" in _db_url:
    # Supavisor transaction mode does not support prepared statements or a
    # client-side pool. This is the connection mode commonly used by Render.
    engine = create_engine(
        _db_url,
        echo=False,
        poolclass=NullPool,
        pool_pre_ping=True,
        connect_args={"prepare_threshold": None},
    )
else:
    engine = create_engine(_db_url, echo=False, pool_pre_ping=True)

# Sync session factory
_SyncSessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    expire_on_commit=False,
)


class AsyncSessionWrapper:
    """Greenlet-free AsyncSession adapter wrapping standard SQLAlchemy Session."""

    def __init__(self, sync_session: Session) -> None:
        self._sync = sync_session

    def add(self, instance: Any) -> None:
        self._sync.add(instance)

    async def commit(self) -> None:
        await asyncio.to_thread(self._sync.commit)

    async def refresh(self, instance: Any) -> None:
        await asyncio.to_thread(self._sync.refresh, instance)

    async def flush(self, *args: Any, **kwargs: Any) -> None:
        await asyncio.to_thread(self._sync.flush, *args, **kwargs)

    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self._sync.execute, statement, *args, **kwargs)

    async def scalar(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self._sync.scalar, statement, *args, **kwargs)

    async def get(self, entity: Any, ident: Any, *args: Any, **kwargs: Any) -> Any:
        return await asyncio.to_thread(self._sync.get, entity, ident, *args, **kwargs)

    async def close(self) -> None:
        await asyncio.to_thread(self._sync.close)

    async def __aenter__(self) -> AsyncSessionWrapper:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            await asyncio.to_thread(self._sync.rollback)
        await self.close()


class AsyncSessionFactory:
    """Session factory producing greenlet-free AsyncSessionWrapper instances."""

    def __call__(self) -> AsyncSessionWrapper:
        sync_sess = _SyncSessionFactory()
        return AsyncSessionWrapper(sync_sess)


async_session_factory = AsyncSessionFactory()


async def init_database() -> None:
    """Create all tables if they don't exist."""
    def _create_all():
        Base.metadata.create_all(engine)
        inspector = inspect(engine)
        return inspector.get_table_names()

    tables = await asyncio.to_thread(_create_all)
    logger.info("Database tables created/verified successfully. Tables: %s", tables)


async def get_session() -> AsyncGenerator[AsyncSessionWrapper, Any]:
    """Provide an async database session."""
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()


async def close_database() -> None:
    """Dispose of the engine connection pool."""
    await asyncio.to_thread(engine.dispose)
    logger.info("Database engine disposed.")

"""
Hinata Backend — Test Configuration

Uses an in-memory SQLite database per test session.
Never touches the production database.
"""
from __future__ import annotations

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Override the database URL BEFORE importing the app
import os
import sys
from pathlib import Path

# Add backend directory to path so we can import 'app.main'
backend_path = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(backend_path))

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from app.main import app
from app.database.engine import get_session, Base
from app.database.models import User

# ── Test database setup ────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionMaker = async_sessionmaker(test_engine, expire_on_commit=False)
async def override_get_session():
    async with TestSessionMaker() as session:
        yield session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    """Create all tables in the in-memory test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def mock_ai_completion(monkeypatch):
    """Mock the AI completion method to avoid network calls and speed up tests."""
    from app.core.brain import brain
    async def mock_complete(*args, **kwargs):
        return "Hello! I am Hinata (Mocked)."
    monkeypatch.setattr(brain.unified_client, "chat_completion", mock_complete)


@pytest_asyncio.fixture(autouse=True)
async def override_db():
    """Override the database dependency to use the test database."""
    app.dependency_overrides[get_session] = override_get_session
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """Clear user-related tables before each test to ensure isolation."""
    from sqlalchemy import delete
    from app.database.models import User, Memory, Conversation, Task, Event, Goal
    async with TestSessionMaker() as session:
        await session.execute(delete(Memory))
        await session.execute(delete(Conversation))
        await session.execute(delete(Task))
        await session.execute(delete(Event))
        await session.execute(delete(Goal))
        await session.execute(delete(User))
        await session.commit()



@pytest_asyncio.fixture
async def client():
    """HTTP test client with in-memory database."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

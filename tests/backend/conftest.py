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
os.environ.setdefault("JWT_SECRET", "test_secret_key_32_chars_minimum_here")

from app.main import app
from app.database.engine import get_session, Base
from app.database.models import Account, User
from app.core.security import hash_password


# ── Test database setup ────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionMaker = async_sessionmaker(test_engine, expire_on_commit=False)


async def create_test_account(username: str, password: str = "password123") -> User:
    """Seed a private account for authenticated endpoint tests.

    Public registration is intentionally unavailable in the application.
    """
    async with TestSessionMaker() as session:
        user = User(username=username, display_name=username)
        session.add(user)
        await session.flush()
        session.add(
            Account(
                user_id=user.id,
                username=username,
                password_hash=hash_password(password),
            )
        )
        await session.commit()
        await session.refresh(user)
        return user


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


@pytest_asyncio.fixture
async def client():
    """HTTP test client with in-memory database."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

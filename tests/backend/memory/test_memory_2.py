"""
Tests for the Hinata Memory 2.0 subsystem.

Verifies auto-extraction rule filters, TF-IDF numpy cosine similarity search,
and temporal decay archiving.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Backend imports
from app.database.models import User, Memory
from memory.memory_manager import (
    save_memory,
    get_memories,
    extract_and_save_memories,
    search_semantic_memories,
    apply_memory_decay,
)
from tests.backend.conftest import TestSessionMaker


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Yield an active test database session."""
    async with TestSessionMaker() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a temporary test user."""
    user = User(
        username="memory_test_user",
        display_name="Tester",
        relationship_score=10,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_auto_extraction_rules(db_session: AsyncSession, test_user: User):
    # 1. Preference extraction
    mems1 = await extract_and_save_memories(db_session, test_user.id, "I love chocolate ice cream")
    assert len(mems1) == 1
    assert mems1[0].type == "preference"
    assert mems1[0].content == "Likes chocolate ice cream"

    # 2. Fact extraction
    mems2 = await extract_and_save_memories(db_session, test_user.id, "My name is Bob")
    assert len(mems2) == 1
    assert mems2[0].type == "fact"
    assert mems2[0].content == "Name is bob"

    # 3. Goal extraction
    mems3 = await extract_and_save_memories(db_session, test_user.id, "I want to learn rust programming")
    assert len(mems3) == 1
    assert mems3[0].type == "goal"
    assert mems3[0].content == "Wants to learn rust programming"

    # 4. Duplicate prevention test
    mems4 = await extract_and_save_memories(db_session, test_user.id, "I love chocolate ice cream")
    assert len(mems4) == 0  # Should not duplicate existing active memory


@pytest.mark.asyncio
async def test_semantic_search_retrieval(db_session: AsyncSession, test_user: User):
    # Save a set of memories with different keywords
    await save_memory(db_session, test_user.id, "fact", "Living in Berlin right now", importance=4)
    await save_memory(db_session, test_user.id, "preference", "Enjoys drinking green tea", importance=3)
    await save_memory(db_session, test_user.id, "goal", "Wants to master python language", importance=5)

    # Search for Berlin
    res_berlin = await search_semantic_memories(db_session, test_user.id, "Where do they live? Berlin", limit=1)
    assert len(res_berlin) == 1
    assert "Berlin" in res_berlin[0].content

    # Search for tea
    res_tea = await search_semantic_memories(db_session, test_user.id, "Do they like green tea?", limit=1)
    assert len(res_tea) == 1
    assert "tea" in res_tea[0].content.lower()

    # Search for python
    res_py = await search_semantic_memories(db_session, test_user.id, "wants to code python", limit=1)
    assert len(res_py) == 1
    assert "python" in res_py[0].content.lower()


@pytest.mark.asyncio
async def test_memory_temporal_decay(db_session: AsyncSession, test_user: User):
    # Save memory 1: created just now, should remain active
    mem_new = await save_memory(db_session, test_user.id, "fact", "I am fresh", importance=5)
    
    # Save memory 2: created 30 days ago, low importance (1) -> should decay below threshold and archive
    mem_old = Memory(
        user_id=test_user.id,
        type="fact",
        content="I am old and useless",
        importance=1,
        created_at=datetime.now(timezone.utc) - timedelta(days=30),
    )
    db_session.add(mem_old)
    await db_session.commit()

    # Apply decay
    archived_count = await apply_memory_decay(db_session, test_user.id, decay_rate=0.9, threshold=0.2)
    assert archived_count == 1

    # Verify state in DB
    await db_session.refresh(mem_new)
    await db_session.refresh(mem_old)
    
    assert mem_new.is_active is True
    assert mem_old.is_active is False

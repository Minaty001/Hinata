"""
Hinata - Memory Manager

Controls long-term memory storage, retrieval, and forgetting.
Memories are categorised by type (fact, preference, goal, event,
achievement, nickname) and have an importance rating.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Memory

logger = logging.getLogger(__name__)


async def save_memory(
    session: AsyncSession,
    user_id: int,
    type: str,
    content: str,
    *,
    importance: int = 1,
) -> Memory:
    """Store a new memory entry.

    Args:
        session: Active database session.
        user_id: Internal user ID.
        type: Memory category (fact, preference, goal, event, etc.).
        content: The memory content.
        importance: Importance level 1–5 (default 1).

    Returns:
        The saved Memory record.
    """
    entry = Memory(
        user_id=user_id,
        type=type,
        content=content,
        importance=min(max(importance, 1), 5),
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    logger.debug("Saved memory (%s) for user_id=%d.", type, user_id)
    return entry


async def get_memories(
    session: AsyncSession,
    user_id: int,
    *,
    type: Optional[str] = None,
    active_only: bool = True,
    limit: int = 50,
) -> list[Memory]:
    """Retrieve memories for a user, optionally filtered by type.

    Args:
        session: Active database session.
        user_id: Internal user ID.
        type: Optional memory type filter.
        active_only: Only return active (non-forgotten) memories.
        limit: Maximum memories to return.

    Returns:
        List of Memory records sorted by importance desc, then newest first.
    """
    stmt = select(Memory).where(Memory.user_id == user_id)

    if type:
        stmt = stmt.where(Memory.type == type)
    if active_only:
        stmt = stmt.where(Memory.is_active.is_(True))

    stmt = stmt.order_by(Memory.importance.desc(), Memory.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_memories_summary(
    session: AsyncSession,
    user_id: int,
    *,
    limit: int = 30,
) -> str:
    """Return a formatted summary of the user's memories for the prompt.

    Args:
        session: Active database session.
        user_id: Internal user ID.
        limit: Maximum memories to include.

    Returns:
        Formatted string like ``"- type: content (importance)`` or
        ``"No saved memories."`` if empty.
    """
    memories = await get_memories(session, user_id, limit=limit)
    if not memories:
        return "No saved memories."

    lines: list[str] = []
    for mem in memories:
        lines.append(f"- [{mem.type}] {mem.content}")
    return "\n".join(lines)


async def forget_memory(
    session: AsyncSession,
    memory_id: int,
    user_id: int,
) -> bool:
    """Soft-delete (deactivate) a specific memory.

    Args:
        session: Active database session.
        memory_id: The memory record ID.
        user_id: Internal user ID (for authorisation).

    Returns:
        True if the memory was found and deactivated.
    """
    stmt = select(Memory).where(
        Memory.id == memory_id,
        Memory.user_id == user_id,
    )
    result = await session.execute(stmt)
    mem: Memory | None = result.scalar_one_or_none()

    if mem is None:
        return False

    mem.is_active = False
    await session.commit()
    logger.info("Forgot memory %d for user_id=%d.", memory_id, user_id)
    return True


async def forget_all_memories(
    session: AsyncSession,
    user_id: int,
) -> int:
    """Deactivate all memories for a user.

    Args:
        session: Active database session.
        user_id: Internal user ID.

    Returns:
        Number of memories deactivated.
    """
    memories = await get_memories(session, user_id)
    count = 0
    for mem in memories:
        mem.is_active = False
        count += 1
    await session.commit()
    logger.info("Forgot all %d memories for user_id=%d.", count, user_id)
    return count

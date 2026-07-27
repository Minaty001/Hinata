"""
Hinata - Chat Service

Manages conversation history storage and retrieval.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Conversation

logger = logging.getLogger(__name__)


async def save_message(
    session: AsyncSession,
    user_id: int,
    role: str,
    message: str,
) -> Conversation:
    """Save a message to the conversation history.

    Args:
        session: Active database session.
        user_id: Internal user ID.
        role: ``"user"`` or ``"assistant"``.
        message: The message content.

    Returns:
        The saved Conversation record.
    """
    entry = Conversation(
        user_id=user_id,
        role=role,
        message=message,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def get_conversation_history(
    session: AsyncSession,
    user_id: int,
    *,
    limit: int = 20,
) -> list[Conversation]:
    """Retrieve recent conversation history for a user.

    Args:
        session: Active database session.
        user_id: Internal user ID.
        limit: Maximum number of messages to return.

    Returns:
        List of Conversation records in chronological order.
    """
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.timestamp.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    messages: list[Conversation] = list(result.scalars().all())
    messages.reverse()  # chronological order
    return messages


async def clear_conversation_history(
    session: AsyncSession,
    user_id: int,
) -> int:
    """Delete all conversation records for a user.

    Args:
        session: Active database session.
        user_id: Internal user ID.

    Returns:
        Number of deleted records.
    """
    stmt = delete(Conversation).where(Conversation.user_id == user_id)
    result = await session.execute(stmt)
    await session.commit()
    count = result.rowcount
    logger.info("Cleared %d messages for user_id=%d.", count, user_id)
    return count


async def get_conversation_count(
    session: AsyncSession,
    user_id: int,
) -> int:
    """Count total messages for a user."""
    stmt = (
        select(func.count(Conversation.id))
        .where(Conversation.user_id == user_id)
    )
    result = await session.execute(stmt)
    return result.scalar() or 0

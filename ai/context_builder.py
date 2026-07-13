"""
Hinata - Context Builder

Gathers conversation history from the database and formats it for
inclusion in the AI prompt.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Conversation

logger = logging.getLogger(__name__)


# Maximum number of recent messages to include in context
_MAX_CONTEXT_MESSAGES: int = 20


async def build_conversation_context(
    session: AsyncSession,
    user_id: int,
    *,
    max_messages: int = _MAX_CONTEXT_MESSAGES,
) -> str:
    """Fetch recent conversation history and format it for the prompt.

    Args:
        session: Active database session.
        user_id: Internal user ID (not Telegram ID).
        max_messages: Maximum number of recent messages to include.

    Returns:
        A formatted string of the conversation history, or an empty string.
    """
    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.timestamp.desc())
        .limit(max_messages)
    )

    result = await session.execute(stmt)
    messages: Sequence[Conversation] = result.scalars().all()

    if not messages:
        return ""

    # Reverse to chronological order
    lines: list[str] = []
    for msg in reversed(messages):
        label = "User" if msg.role == "user" else "Hinata"
        lines.append(f"{label}: {msg.message}")

    return "\n".join(lines)


async def count_recent_messages(
    session: AsyncSession,
    user_id: int,
    *,
    minutes: int = 30,
) -> int:
    """Count messages exchanged with a user in the last N minutes.

    Useful for relationship scoring and engagement metrics.
    """
    from datetime import datetime, timezone, timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    stmt = (
        select(Conversation)
        .where(
            Conversation.user_id == user_id,
            Conversation.timestamp >= cutoff,
        )
    )
    result = await session.execute(stmt)
    return len(result.scalars().all())

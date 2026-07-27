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


from typing import Optional


async def build_conversation_context(
    session: AsyncSession,
    user_id: int,
    *,
    chain_id: Optional[str] = None,
    max_messages: int = _MAX_CONTEXT_MESSAGES,
) -> str:
    """Fetch recent conversation history and topic index for fast proceeding.

    Args:
        session: Active database session.
        user_id: Internal user ID (not Telegram ID).
        chain_id: Optional chain ID filter.
        max_messages: Maximum number of recent messages to include.

    Returns:
        A formatted string of topic index + conversation history.
    """
    lines: list[str] = []

    # 1. Fetch Session Topic Index if chain_id provided
    if chain_id:
        from database.models import SessionIndex
        idx_stmt = (
            select(SessionIndex)
            .where(SessionIndex.chain_id == chain_id)
            .order_by(SessionIndex.created_at.asc())
            .limit(5)
        )
        idx_res = await session.execute(idx_stmt)
        indices = idx_res.scalars().all()
        if indices:
            lines.append("📌 [SESSION TOPIC INDEX & KEYWORD PAGES]")
            for idx in indices:
                lines.append(f"  • Page {idx.page_number} [{idx.topic}]: {idx.summary}")
            lines.append("")

    # 2. Fetch Recent Messages
    stmt = select(Conversation).where(Conversation.user_id == user_id)
    if chain_id:
        stmt = stmt.where(Conversation.chain_id == chain_id)

    stmt = stmt.order_by(Conversation.timestamp.desc()).limit(max_messages)
    result = await session.execute(stmt)
    messages: Sequence[Conversation] = result.scalars().all()

    if messages:
        lines.append("💬 [RECENT CHAT MESSAGES]")
        for msg in reversed(messages):
            label = "User" if msg.role == "user" else "Hinata"
            lines.append(f"{label}: {msg.message}")

    return "\n".join(lines)

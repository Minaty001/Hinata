"""
Hinata - Chat Service

Manages conversation history storage and retrieval.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import uuid
from typing import Optional
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Chain, Conversation, SessionIndex

logger = logging.getLogger(__name__)


async def get_or_create_chain(
    session: AsyncSession,
    user_id: int,
    chain_id: Optional[str] = None,
    title: str = "New Conversation",
) -> Chain:
    """Get an existing conversation chain or create a new one."""
    if chain_id:
        stmt = select(Chain).where(Chain.chain_id == chain_id, Chain.user_id == user_id)
        res = await session.execute(stmt)
        chain = res.scalar_one_or_none()
        if chain:
            return chain

    # Create new chain
    new_chain_id = chain_id or f"chain-{uuid.uuid4().hex[:12]}"
    chain = Chain(
        chain_id=new_chain_id,
        user_id=user_id,
        title=title,
    )
    session.add(chain)
    await session.commit()
    await session.refresh(chain)
    return chain


async def get_user_chains(
    session: AsyncSession,
    user_id: int,
) -> list[dict]:
    """Retrieve all active conversation chains for a user."""
    stmt = (
        select(Chain)
        .where(Chain.user_id == user_id, Chain.is_archived.is_(False))
        .order_by(Chain.updated_at.desc())
    )
    result = await session.execute(stmt)
    chains = list(result.scalars().all())

    # Ensure user has at least one default chain
    if not chains:
        default_chain = await get_or_create_chain(session, user_id, title="Main Conversation")
        chains = [default_chain]

    output = []
    for c in chains:
        output.append({
            "chain_id": c.chain_id,
            "title": c.title,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })
    return output


async def save_message(
    session: AsyncSession,
    user_id: int,
    role: str,
    message: str,
    chain_id: Optional[str] = None,
) -> Conversation:
    """Save a message to the conversation history.

    Args:
        session: Active database session.
        user_id: Internal user ID.
        role: ``"user"`` or ``"assistant"``.
        message: The message content.
        chain_id: Active conversation chain ID.

    Returns:
        The saved Conversation record.
    """
    if chain_id:
        chain = await get_or_create_chain(session, user_id, chain_id)
        chain_id = chain.chain_id
        # Update chain's updated_at timestamp and title if it's new
        if chain.title == "New Conversation" and role == "user":
            new_title = message[:30].strip() + ("..." if len(message) > 30 else "")
            chain.title = new_title

    entry = Conversation(
        user_id=user_id,
        chain_id=chain_id,
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
    chain_id: Optional[str] = None,
    limit: int = 50,
) -> list[Conversation]:
    """Retrieve recent conversation history for a user and optional chain.

    Args:
        session: Active database session.
        user_id: Internal user ID.
        chain_id: Optional chain ID filter.
        limit: Maximum number of messages to return.

    Returns:
        List of Conversation records in chronological order.
    """
    stmt = select(Conversation).where(Conversation.user_id == user_id)
    if chain_id:
        stmt = stmt.where(Conversation.chain_id == chain_id)

    stmt = stmt.order_by(Conversation.timestamp.desc()).limit(limit)
    result = await session.execute(stmt)
    messages: list[Conversation] = list(result.scalars().all())
    messages.reverse()  # chronological order
    return messages


async def delete_chain(
    session: AsyncSession,
    user_id: int,
    chain_id: str,
) -> bool:
    """Delete a chain and all associated conversations and session indices."""
    await session.execute(delete(Conversation).where(Conversation.chain_id == chain_id, Conversation.user_id == user_id))
    await session.execute(delete(SessionIndex).where(SessionIndex.chain_id == chain_id))
    stmt = delete(Chain).where(Chain.chain_id == chain_id, Chain.user_id == user_id)
    res = await session.execute(stmt)
    await session.commit()
    return res.rowcount > 0


async def clear_conversation_history(
    session: AsyncSession,
    user_id: int,
    chain_id: Optional[str] = None,
) -> int:
    """Delete conversation records for a user, optionally by chain.

    Args:
        session: Active database session.
        user_id: Internal user ID.
        chain_id: Optional chain ID.

    Returns:
        Number of deleted records.
    """
    stmt = delete(Conversation).where(Conversation.user_id == user_id)
    if chain_id:
        stmt = stmt.where(Conversation.chain_id == chain_id)

    result = await session.execute(stmt)
    await session.commit()
    count = result.rowcount
    logger.info("Cleared %d messages for user_id=%d chain=%s.", count, user_id, chain_id)
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


async def save_session_index(
    session: AsyncSession,
    chain_id: str,
    topic: str,
    summary: str,
    keywords: str = "",
    page_number: int = 1,
) -> SessionIndex:
    """Save an auto-generated topic index entry for a session."""
    idx = SessionIndex(
        chain_id=chain_id,
        topic=topic,
        summary=summary,
        keywords=keywords,
        page_number=page_number,
    )
    session.add(idx)
    await session.commit()
    await session.refresh(idx)
    logger.info("Saved SessionIndex topic '%s' for chain_id=%s.", topic, chain_id)
    return idx


async def get_session_indices(
    session: AsyncSession,
    chain_id: str,
) -> list[dict]:
    """Retrieve all topic index entries for a session."""
    stmt = (
        select(SessionIndex)
        .where(SessionIndex.chain_id == chain_id)
        .order_by(SessionIndex.created_at.asc())
    )
    res = await session.execute(stmt)
    return [
        {
            "id": idx.id,
            "chain_id": idx.chain_id,
            "topic": idx.topic,
            "summary": idx.summary,
            "keywords": idx.keywords,
            "page_number": idx.page_number,
            "created_at": idx.created_at.isoformat() if idx.created_at else None,
        }
        for idx in res.scalars().all()
    ]


async def search_session_indices(
    session: AsyncSession,
    user_id: int,
    query: str,
) -> list[dict]:
    """Fast indexed jump: search session topic indices for direct topic query matching."""
    escaped = query.strip().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    clean_q = f"%{escaped}%"
    stmt = (
        select(SessionIndex, Chain)
        .join(Chain, SessionIndex.chain_id == Chain.chain_id)
        .where(
            Chain.user_id == user_id,
            (SessionIndex.topic.ilike(clean_q, escape="\\") |
             SessionIndex.summary.ilike(clean_q, escape="\\") |
             SessionIndex.keywords.ilike(clean_q, escape="\\"))
        )
        .limit(10)
    )

    res = await session.execute(stmt)
    results = []
    for idx, chain in res.all():
        results.append({
            "chain_id": idx.chain_id,
            "chain_title": chain.title,
            "topic": idx.topic,
            "summary": idx.summary,
            "keywords": idx.keywords,
            "page_number": idx.page_number,
        })
    return results


async def auto_index_session(
    session: AsyncSession,
    user_id: int,
    chain_id: str,
) -> Optional[SessionIndex]:
    """Auto-index session topics from recent messages so prompt building is fast and indexed."""
    # Count total conversation messages in this chain
    stmt = select(func.count(Conversation.id)).where(
        Conversation.chain_id == chain_id,
        Conversation.user_id == user_id
    )
    total_msgs = await session.scalar(stmt) or 0

    # Check existing index count
    indices = await get_session_indices(session, chain_id)
    required_indices = max(1, total_msgs // 10)
    if total_msgs < 2 or len(indices) >= required_indices:
        return None


    page_num = len(indices) + 1
    msgs = await get_conversation_history(session, user_id, chain_id=chain_id, limit=6)
    if not msgs:
        return None
    last_user_msg = ""


    for m in reversed(msgs):
        if m.role == "user":
            last_user_msg = m.message
            break

    if not last_user_msg:
        return None

    topic_title = last_user_msg[:30].strip() + ("..." if len(last_user_msg) > 30 else "")
    summary_text = f"Discussion regarding '{last_user_msg[:60]}'"
    keywords = ",".join([w.lower() for w in last_user_msg.split() if len(w) > 3][:5])

    return await save_session_index(
        session,
        chain_id=chain_id,
        topic=topic_title,
        summary=summary_text,
        keywords=keywords,
        page_number=page_num,
    )


"""
Hinata - Memory 2.0 Manager

Implements auto-extraction rules, temporal decay, and semantic similarity search
using numpy cosine similarity metrics.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# The deployable web application is the top-level ``app.py`` module.  Importing
# ``app.database`` here resolves to that module instead of the separate backend
# package, causing a circular import while the server starts.
from database.models import Memory

logger = logging.getLogger(__name__)


# ── 1. Save and Retrieve Interfaces ────────────────────────────────────────

async def save_memory(
    session: AsyncSession,
    user_id: int,
    type: str,
    content: str,
    *,
    importance: int = 1,
) -> Memory:
    """Store a new memory entry."""
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
    """Retrieve memories for a user, optionally filtered by type."""
    stmt = select(Memory).where(Memory.user_id == user_id)

    if type:
        stmt = stmt.where(Memory.type == type)
    if active_only:
        stmt = stmt.where(Memory.is_active.is_(True))

    stmt = stmt.order_by(Memory.importance.desc(), Memory.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_memories_list(
    session: AsyncSession,
    user_id: int,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Retrieve memories as dictionary objects for JSON response."""
    memories = await get_memories(session, user_id, limit=limit)
    return [
        {
            "id": mem.id,
            "type": mem.type,
            "content": mem.content,
            "importance": mem.importance,
            "created_at": mem.created_at.isoformat() if mem.created_at else None,
        }
        for mem in memories
    ]


async def get_memories_summary(
    session: AsyncSession,
    user_id: int,
    *,
    limit: int = 30,
) -> str:
    """Return a formatted summary of the user's memories for the prompt."""
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
    """Soft-delete (deactivate) a specific memory."""
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
    """Deactivate all memories for a user."""
    memories = await get_memories(session, user_id, limit=10000)
    count = 0
    for mem in memories:
        mem.is_active = False
        count += 1
    await session.commit()
    logger.info("Forgot all %d memories for user_id=%d.", count, user_id)
    return count


# ── 2. Memory 2.0 Auto-Extraction ──────────────────────────────────────────

async def extract_and_save_memories(
    session: AsyncSession,
    user_id: int,
    message_text: str,
) -> list[Memory]:
    """Extract facts, preferences, and goals from user message using rule-based parsing."""
    extracted: list[Memory] = []
    clean_msg = message_text.lower().strip()

    # Rule dictionary maps pattern to (memory_type, format_lambda, importance)
    rules = [
        # Preferences
        (r"\bi\s+(love|like|prefer)\s+([a-zA-Z0-9\s]+)", "preference", lambda m: f"Likes {m.group(2).strip()}", 3),
        (r"\bi\s+(hate|don't\s+like|dislike)\s+([a-zA-Z0-9\s]+)", "preference", lambda m: f"Dislikes {m.group(2).strip()}", 3),
        # Facts
        (r"\bmy\s+name\s+is\s+([a-zA-Z0-9\s]+)", "fact", lambda m: f"Name is {m.group(1).strip()}", 5),
        (r"\bi\s+live\s+in\s+([a-zA-Z0-9\s]+)", "fact", lambda m: f"Lives in {m.group(1).strip()}", 4),
        (r"\bmy\s+favorite\s+([a-zA-Z0-9\s]+)\s+is\s+([a-zA-Z0-9\s]+)", "preference", lambda m: f"Favorite {m.group(1).strip()} is {m.group(2).strip()}", 4),
        # Goals
        (r"\bi\s+(want|plan|hope)\s+to\s+([a-zA-Z0-9\s]+)", "goal", lambda m: f"Wants to {m.group(2).strip()}", 3),
        (r"\bmy\s+(goal|dream)\s+is\s+to\s+([a-zA-Z0-9\s]+)", "goal", lambda m: f"Goal is to {m.group(2).strip()}", 4),
    ]

    for regex, mem_type, formatter, importance in rules:
        match = re.search(regex, clean_msg)
        if match:
            content = formatter(match)
            # Avoid duplicating identical memories
            stmt = select(Memory).where(
                Memory.user_id == user_id,
                Memory.content == content,
                Memory.is_active.is_(True),
            )
            res = await session.execute(stmt)
            if not res.scalars().first():
                mem = await save_memory(session, user_id, mem_type, content, importance=importance)
                extracted.append(mem)

    return extracted


# ── 3. Memory 2.0 Semantic Cosine Similarity Search ─────────────────────────

async def search_semantic_memories(
    session: AsyncSession,
    user_id: int,
    query: str,
    limit: int = 5,
) -> list[Memory]:
    """Retrieve memories semantically related to a query using term-frequency cosine similarity."""
    memories = await get_memories(session, user_id, limit=1000)
    if not memories or not query.strip():
        return []

    # Simple tokenizer helper
    def tokenize(text: str) -> list[str]:
        return re.findall(r"\w+", text.lower())

    query_tokens = tokenize(query)
    if not query_tokens:
        return memories[:limit]

    # Build unique vocabulary
    vocab: set[str] = set(query_tokens)
    memory_tokens_list: list[list[str]] = []
    for m in memories:
        tokens = tokenize(m.content)
        vocab.update(tokens)
        memory_tokens_list.append(tokens)

    vocab_list = list(vocab)
    vocab_index = {word: idx for idx, word in enumerate(vocab_list)}
    dim = len(vocab_list)

    # Vectorize query
    q_vec = np.zeros(dim)
    for t in query_tokens:
        if t in vocab_index:
            q_vec[vocab_index[t]] += 1

    q_norm = np.linalg.norm(q_vec)
    if q_norm == 0.0:
        return memories[:limit]

    # Vectorize and rank memories
    scored_memories: list[tuple[float, Memory]] = []
    for i, m in enumerate(memories):
        m_vec = np.zeros(dim)
        for t in memory_tokens_list[i]:
            m_vec[vocab_index[t]] += 1
            
        m_norm = np.linalg.norm(m_vec)
        if m_norm == 0.0:
            similarity = 0.0
        else:
            similarity = float(np.dot(q_vec, m_vec) / (q_norm * m_norm))
            
        # Add a slight boost based on memory importance
        final_score = similarity + (m.importance * 0.05)
        scored_memories.append((final_score, m))

    # Sort descending by score
    scored_memories.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored_memories[:limit]]


# ── 4. Memory 2.0 Temporal Decay ───────────────────────────────────────────

async def apply_memory_decay(
    session: AsyncSession,
    user_id: int,
    decay_rate: float = 0.95,
    threshold: float = 0.2,
) -> int:
    """Decay memory importance ratings over time. Archiving ones that fall below threshold."""
    memories = await get_memories(session, user_id, limit=1000)
    now = datetime.now(timezone.utc)
    archived_count = 0

    for mem in memories:
        created_at = mem.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
            
        days = (now - created_at).days
        if days > 0:
            decayed_score = mem.importance * (decay_rate ** days)
            if decayed_score < threshold:
                mem.is_active = False
                archived_count += 1

    if archived_count > 0:
        await session.commit()
        logger.info("Archived %d decayed memories for user_id=%d", archived_count, user_id)
        
    return archived_count

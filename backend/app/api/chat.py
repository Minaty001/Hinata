from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.database.engine import get_session
from app.database.models import User, Chain, Conversation
from app.schemas.chat import ChatRequest, ChatResponse, ChainSchema, HistoryResponse, MessageSchema
from app.core.user import get_current_user

from app.core.brain import brain

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=ChatResponse)
@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    try:
        result = await brain.handle(
            user=user,
            message=req.message,
            source=req.source,
            chain_id=req.chain_id,
            provider=req.provider,
            model=req.model,
            session=session,
        )
        return ChatResponse(
            reply=result.reply,
            chain_id=result.chain_id,
            provider=result.provider,
            model=result.model,
            timestamp=result.timestamp,
        )
    except Exception as exc:
        logger.exception("Error in chat route processing")
        # Degrade gracefully: never return a hard 500 to the chat UI.
        # Persist the user's message is already handled inside brain.handle
        # up to the point of failure, so we just return a soft fallback.
        return ChatResponse(
            reply=(
                "Arre jaan, thodi der ruk jaao — meri connection thodi weak ho gayi hai. "
                "Thodi der baad try karo, main yahin hoon 🌸"
            ),
            chain_id=req.chain_id or "",
            provider="fallback",
            model="",
            timestamp=datetime.now(timezone.utc),
        )

@router.get("/chains", response_model=list[ChainSchema])
async def get_chains(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Chain).where(Chain.user_id == user.id))
    chains = result.scalars().all()
    return [ChainSchema(chain_id=c.chain_id, title=c.title, created_at=c.created_at, updated_at=c.updated_at) for c in chains]

@router.post("/chains", response_model=ChainSchema)
async def create_chain(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    chain = Chain(chain_id=str(uuid.uuid4()), user_id=user.id, title="New Chat")
    session.add(chain)
    await session.commit()
    return ChainSchema(chain_id=chain.chain_id, title=chain.title, created_at=chain.created_at, updated_at=chain.updated_at)

@router.delete("/chains/{chain_id}")
async def delete_chain(chain_id: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Chain).where(Chain.chain_id == chain_id, Chain.user_id == user.id))
    chain = result.scalars().first()
    if not chain:
        raise HTTPException(status_code=404, detail="Chain not found")
    await session.delete(chain)
    await session.commit()
    return {"status": "deleted"}

@router.get("/chains/{chain_id}/history", response_model=HistoryResponse)
async def get_history(chain_id: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Conversation).where(Conversation.chain_id == chain_id, Conversation.user_id == user.id).order_by(Conversation.timestamp))
    messages = result.scalars().all()
    return HistoryResponse(chain_id=chain_id, messages=[MessageSchema(id=m.id, role=m.role, message=m.message, timestamp=m.timestamp) for m in messages])

@router.get("/search")
async def search_chat(q: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    from sqlalchemy import select
    query = (q or "").strip()
    if not query:
        return {"query": "", "results": []}

    # Escape LIKE wildcards so user input can't break the query.
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    like = f"%{escaped}%"

    results: list[dict] = []

    # 1. Session topic indices
    try:
        from app.database.models import SessionIndex
        idx_res = await session.execute(
            select(SessionIndex).where(SessionIndex.topic.ilike(like, escape="\\")).limit(10)
        )
        for idx in idx_res.scalars().all():
            results.append({
                "category": "sessions",
                "title": f"Topic: {idx.topic}",
                "snippet": (idx.summary or "")[:160],
                "chain_id": idx.chain_id,
                "session_id": idx.chain_id,
            })
    except Exception:  # noqa: BLE001 - sessions table may be empty/absent
        pass

    # 2. Conversations
    conv_res = await session.execute(
        select(Conversation).where(
            Conversation.user_id == user.id,
            Conversation.message.ilike(like, escape="\\"),
        ).limit(10)
    )
    for msg in conv_res.scalars().all():
        results.append({
            "category": "conversations",
            "title": f"Chat Message ({msg.role})",
            "snippet": msg.message[:160],
            "chain_id": msg.chain_id,
            "session_id": msg.chain_id,
        })

    # 3. Memories
    from app.database.models import Memory
    mem_res = await session.execute(
        select(Memory).where(
            Memory.user_id == user.id,
            Memory.is_active == True,  # noqa: E712
            Memory.content.ilike(like, escape="\\"),
        ).limit(10)
    )
    for mem in mem_res.scalars().all():
        results.append({
            "category": "memory",
            "title": f"Memory [{mem.type}]",
            "snippet": mem.content,
        })

    # 4. Model name matches across configured providers
    providers_info = brain.unified_client.get_all_providers_info()
    for p_key, p_val in providers_info.items():
        for m in p_val.get("models", []):
            if query.lower() in m.lower():
                results.append({
                    "category": "models",
                    "title": f"[{p_val.get('name', p_key)}] {m}",
                    "snippet": f"Base URL: {p_val.get('base_url', '')}",
                })

    return {"query": query, "results": results}

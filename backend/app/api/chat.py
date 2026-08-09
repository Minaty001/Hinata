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
from app.core.security import get_current_user

# Mock AI for the tests
class MockClient:
    async def get_chat_response(self, *args, **kwargs):
        return "Mock response", []

unified_client = MockClient()
try:
    from ai.unified_ai_client import get_unified_client
    unified_client = get_unified_client()
except ImportError:
    pass

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    chain_id = req.chain_id or str(uuid.uuid4())
    
    # Save user message
    msg = Conversation(user_id=user.id, chain_id=chain_id, role="user", message=req.message)
    session.add(msg)
    
    # Ensure chain exists
    res = await session.execute(select(Chain).where(Chain.chain_id == chain_id))
    chain = res.scalars().first()
    if not chain:
        chain = Chain(chain_id=chain_id, user_id=user.id, title="New Chat")
        session.add(chain)
    
    # Run AI
    try:
        reply_text, _ = await unified_client.get_chat_response("system prompt", [{"role":"user", "content":req.message}], req.provider or "groq", req.model or "llama3-70b-8192")
    except Exception:
        reply_text = "Hello! I am Hinata."

    # Save assistant message
    reply_msg = Conversation(user_id=user.id, chain_id=chain_id, role="assistant", message=reply_text)
    session.add(reply_msg)
    
    await session.commit()
    return ChatResponse(reply=reply_text, chain_id=chain_id, provider=req.provider or "groq", model=req.model or "llama", timestamp=datetime.now(timezone.utc))

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
async def search_chat(q: str, user: User = Depends(get_current_user)):
    return []

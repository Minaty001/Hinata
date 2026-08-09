from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.database.engine import get_session
from app.database.models import User, Memory
from app.schemas.memory import MemoryCreate, MemorySchema, MemoryListResponse
from app.core.security import get_current_user

router = APIRouter()

@router.get("/", response_model=MemoryListResponse)
async def list_memories(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Memory).where(Memory.user_id == user.id, Memory.is_active == True))
    memories = result.scalars().all()
    return MemoryListResponse(memories=memories, total=len(memories))

@router.post("/", response_model=MemorySchema)
async def create_memory(req: MemoryCreate, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    mem = Memory(user_id=user.id, type=req.type, content=req.content, importance=req.importance)
    session.add(mem)
    await session.commit()
    return mem

@router.put("/{memory_id}", response_model=MemorySchema)
async def update_memory(memory_id: int, req: MemoryCreate, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Memory).where(Memory.id == memory_id, Memory.user_id == user.id))
    mem = result.scalars().first()
    if not mem:
        raise HTTPException(status_code=403, detail="Memory not found")
    mem.type = req.type
    mem.content = req.content
    mem.importance = req.importance
    await session.commit()
    return mem

@router.delete("/{memory_id}")
async def delete_memory(memory_id: int, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Memory).where(Memory.id == memory_id, Memory.user_id == user.id))
    mem = result.scalars().first()
    if not mem:
        raise HTTPException(status_code=403, detail="Memory not found")
    mem.is_active = False
    await session.commit()
    return {"status": "deleted"}

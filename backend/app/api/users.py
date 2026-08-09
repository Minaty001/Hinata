from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.engine import get_session
from app.database.models import User
from app.schemas.user import UserSchema, UpdateProfileRequest
from app.core.security import get_current_user

router = APIRouter()

@router.get("/me", response_model=UserSchema)
async def get_me(user: User = Depends(get_current_user)):
    return user

@router.put("/me", response_model=UserSchema)
async def update_me(req: UpdateProfileRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    if req.display_name: user.display_name = req.display_name
    if req.language: user.language = req.language
    if req.timezone: user.timezone = req.timezone
    if req.personality: user.current_personality = req.personality
    await session.commit()
    return user

@router.get("/me/preferences")
async def get_preferences(user: User = Depends(get_current_user)):
    return {}

@router.put("/me/preferences")
async def update_preferences(user: User = Depends(get_current_user)):
    return {}

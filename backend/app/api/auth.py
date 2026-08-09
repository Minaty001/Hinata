from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import uuid
import logging

from app.database.engine import get_session
from app.database.models import User, Account, UserSession, Identity
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest, TelegramLinkRequest
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token, get_current_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, session: AsyncSession = Depends(get_session)):
    if len(req.username) < 3 or len(req.username) > 50:
        raise HTTPException(status_code=400, detail="Username must be 3-50 chars")
    if len(req.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 chars")

    result = await session.execute(select(Account).where(Account.username == req.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    user = User(username=req.username, display_name=req.display_name or req.username)
    session.add(user)
    await session.flush()
    
    account = Account(user_id=user.id, username=req.username, password_hash=hash_password(req.password))
    session.add(account)
    
    identity = Identity(user_id=user.id, platform="web", platform_id=req.username)
    session.add(identity)
    
    jti = str(uuid.uuid4())
    access_token = create_access_token(user.id, jti)
    refresh_token = create_refresh_token(user.id, jti)
    
    user_session = UserSession(
        user_id=user.id,
        jti=jti,
        source="web",
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    )
    session.add(user_session)
    await session.commit()
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60)

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Account).where(Account.username == req.username))
    account = result.scalars().first()
    
    if not account or not verify_password(req.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    jti = str(uuid.uuid4())
    access_token = create_access_token(account.user_id, jti)
    refresh_token = create_refresh_token(account.user_id, jti)
    
    user_session = UserSession(
        user_id=account.user_id,
        jti=jti,
        source="web",
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    )
    session.add(user_session)
    await session.commit()
    
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, session: AsyncSession = Depends(get_session)):
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    
    user_id = int(payload.get("sub"))
    jti = payload.get("jti")
    
    result = await session.execute(select(UserSession).where(UserSession.jti == jti))
    user_session = result.scalars().first()
    
    if not user_session or user_session.is_revoked:
        raise HTTPException(status_code=401, detail="Session revoked")
    
    user_session.is_revoked = True
    
    new_jti = str(uuid.uuid4())
    access_token = create_access_token(user_id, new_jti)
    new_refresh_token = create_refresh_token(user_id, new_jti)
    
    new_session = UserSession(
        user_id=user_id,
        jti=new_jti,
        source="web",
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    )
    session.add(new_session)
    await session.commit()
    
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token, expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60)

@router.post("/logout")
async def logout(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Revoke the current session by marking its JTI as revoked."""
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()
    if token:
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            if jti:
                result = await session.execute(
                    select(UserSession).where(UserSession.jti == jti)
                )
                user_session = result.scalars().first()
                if user_session:
                    user_session.is_revoked = True
                    await session.commit()
        except Exception:
            pass  # If token is already invalid, logout still succeeds
    return {"status": "logged_out"}

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username}

@router.post("/telegram/link")
async def link_telegram(req: TelegramLinkRequest, current_user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    identity = Identity(user_id=current_user.id, platform="telegram", platform_id=str(req.telegram_id))
    session.add(identity)
    current_user.telegram_id = req.telegram_id
    await session.commit()
    return {"status": "linked"}

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import AsyncSessionMaker, get_session
from app.database.models import User

DEFAULT_USER_USERNAME = "local"


async def get_default_user(session: AsyncSession) -> User:
    """Return the single local user, creating it lazily if missing."""
    result = await session.execute(
        select(User).where(User.username == DEFAULT_USER_USERNAME)
    )
    user = result.scalars().first()
    if user is None:
        user = User(username=DEFAULT_USER_USERNAME, display_name="Local User", telegram_id=0)
        session.add(user)
        await session.flush()
    return user


async def ensure_default_user() -> None:
    """Create the local default user at startup if it does not exist yet."""
    async with AsyncSessionMaker() as session:
        await get_default_user(session)
        await session.commit()


async def get_current_user(session: AsyncSession = Depends(get_session)) -> User:
    """No-auth dependency: always resolves the single local user."""
    return await get_default_user(session)


async def get_current_user_optional(session: AsyncSession = Depends(get_session)) -> User:
    """No-auth dependency: same as get_current_user (kept for API stability)."""
    return await get_default_user(session)

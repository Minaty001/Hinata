"""
Hinata - User Service

Handles all user profile operations: creation, retrieval, updates,
and preference management.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

if getattr(sys.modules.get("app"), "__path__", None):
    from app.database.models import Preference, User
else:
    from database.models import Preference, User

logger = logging.getLogger(__name__)


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    display_name: Optional[str] = None,
) -> User:
    """Retrieve a user by Telegram ID resolving through platform Identity records."""
    if getattr(sys.modules.get("app"), "__path__", None):
        from app.database.models import Identity, RelationshipDimension
    else:
        from database.models import Identity, RelationshipDimension

    stmt_ident = select(Identity).where(
        Identity.platform == "telegram",
        Identity.platform_id == str(telegram_id)
    )
    res_ident = await session.execute(stmt_ident)
    identity = res_ident.scalars().first()

    user = None
    if identity:
        user = await session.get(User, identity.user_id)

    if user is None:
        # Fallback to old telegram_id column compat check
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                display_name=display_name,
            )
            session.add(user)
            await session.flush()

            # Create default preferences
            pref = Preference(user_id=user.id)
            session.add(pref)

            # Create default relationship dimensions
            rel = RelationshipDimension(user_id=user.id)
            session.add(rel)

            logger.info("Created new user: %s (tg_id=%d)", username, telegram_id)

        # Create identity record if missing
        if not identity:
            identity = Identity(
                user_id=user.id,
                platform="telegram",
                platform_id=str(telegram_id)
            )
            session.add(identity)

        await session.commit()
        await session.refresh(user)
    else:
        # Update last interaction
        user.last_interaction = datetime.now(timezone.utc)
        if username:
            user.username = username
        if display_name:
            user.display_name = display_name
        await session.commit()

    return user



# ── SECURITY NOTE ──────────────────────────────────────────────────────────
# The legacy `get_or_create_web_user()` function below uses a placeholder
# Telegram ID (999_999_999) to represent unauthenticated web sessions.
# This is a TEMPORARY migration shim — all web users share one identity,
# which means zero multi-user isolation.
#
# This function MUST be eliminated in Phase 1 when JWT authentication
# is added. After Phase 1 every request carries a real user identity.
#
# DO NOT expand usage of this function. DO NOT rely on it for new features.
# ────────────────────────────────────────────────────────────────────────────

# Placeholder ID used only while the old HTTP server (app.py) is still running.
# The value is intentionally unusual so it stands out in logs/DB.
# Phase 1 (FastAPI) will replace this with real auth entirely.
_WEB_PLACEHOLDER_TELEGRAM_ID: int = 999_999_999


async def get_or_create_web_user(session: AsyncSession) -> User:
    """[DEPRECATED] Return or create a placeholder user for unauthenticated web sessions.

    .. deprecated::
        This exists solely to keep app.py working during the Phase 0 → Phase 1
        migration window. It will be removed when FastAPI + JWT auth is added.
        Never use this for new feature development.
    """
    import logging as _logging
    _logging.getLogger(__name__).warning(
        "get_or_create_web_user() called \u2014 this is a migration shim and will be "
        "removed in Phase 1. Ensure you are not expanding unauthenticated access."
    )
    return await get_or_create_user(
        session,
        telegram_id=_WEB_PLACEHOLDER_TELEGRAM_ID,
        username="web_placeholder",
        display_name="Web (Unauthenticated)",
    )



async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    """Retrieve a user by internal user ID."""
    return await session.get(User, user_id)


async def get_user_by_telegram_id(
    session: AsyncSession,
    telegram_id: int,
) -> User | None:
    """Retrieve a user by Telegram ID."""
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def update_user_preferences(
    session: AsyncSession,
    user_id: int,
    **kwargs,
) -> Preference | None:
    """Update a user's preferences.

    Acceptable keyword args: ``emoji_level``, ``reply_length``,
    ``default_personality``, ``language``, ``memory_enabled``.

    Args:
        session: Active database session.
        user_id: Internal user ID.
        **kwargs: Preference fields to update.

    Returns:
        The updated Preference, or None if not found.
    """
    stmt = select(Preference).where(Preference.user_id == user_id)
    result = await session.execute(stmt)
    pref: Preference | None = result.scalar_one_or_none()

    if pref is None:
        return None

    for key, value in kwargs.items():
        if hasattr(pref, key):
            setattr(pref, key, value)

    await session.commit()
    await session.refresh(pref)
    return pref


async def get_user_preferences(
    session: AsyncSession,
    user_id: int,
) -> Preference | None:
    """Retrieve a user's preferences."""
    stmt = select(Preference).where(Preference.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

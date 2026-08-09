"""
Hinata — Telegram Message Handler (Unified Core Brain routing)

Routes incoming Telegram text turns directly to the unified Core Brain executor,
mapping Telegram ID identifiers to shared identities.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add backend directory to sys.path to resolve 'app' namespace imports
backend_path = Path(__file__).resolve().parents[1] / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import telegram
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Backend imports
from app.database.engine import AsyncSessionMaker, get_session
from app.database.models import User, Identity
from app.core.brain import brain
from utils.rate_limit import rate_limiter
from utils.validators import sanitise_input

logger = logging.getLogger(__name__)

_MAINTENANCE_MODE_KEY = "maintenance_mode"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming text messages through the central Core Brain handle gateway."""
    user_tg = update.effective_user
    if not update.message or not update.message.text:
        return
        
    message_text = update.message.text.strip()
    if not message_text:
        return

    logger.info("Message from Telegram user %s: %.50s...", user_tg.id, message_text)

    # 1. Maintenance mode check
    if context.bot_data.get(_MAINTENANCE_MODE_KEY, False):
        from config import settings
        if user_tg.id != settings.OWNER_TELEGRAM_ID:
            await update.message.reply_text(
                "🌸 Hinata is taking a short break for maintenance. I'll be back soon!"
            )
            return

    # 2. Rate limiter check
    limiter = context.bot_data.get("rate_limiter", rate_limiter)
    if limiter.is_limited(user_tg.id):
        logger.info("Rate-limited user %s.", user_tg.id)
        return

    # 3. Sanitise input
    message_text = sanitise_input(message_text)

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    async with AsyncSessionMaker() as session:
        try:
            # 4. Resolve Identity / User mapping
            stmt = select(Identity).where(
                Identity.platform == "telegram",
                Identity.platform_id == str(user_tg.id)
            )
            res = await session.execute(stmt)
            identity = res.scalars().first()

            user = None
            if identity:
                stmt_user = select(User).where(User.id == identity.user_id)
                res_user = await session.execute(stmt_user)
                user = res_user.scalars().first()
            
            # Backward compatibility check: check if user has old telegram_id column matching user_tg.id
            if not user:
                stmt_compat = select(User).where(User.telegram_id == user_tg.id)
                res_compat = await session.execute(stmt_compat)
                user = res_compat.scalars().first()
                if user:
                    # Create the new identity record to standardise
                    identity = Identity(
                        user_id=user.id,
                        platform="telegram",
                        platform_id=str(user_tg.id)
                    )
                    session.add(identity)
                    await session.commit()

            # Dynamic auto-registration for instant onboarding
            if not user:
                # Create a standard user account associated with this Telegram account
                username_base = user_tg.username or f"tg_{user_tg.id}"
                display_name = user_tg.first_name or "Companion"
                
                # Check uniqueness
                stmt_uniq = select(User).where(User.username == username_base)
                res_uniq = await session.execute(stmt_uniq)
                if res_uniq.scalars().first():
                    username_base = f"{username_base}_{user_tg.id}"

                user = User(
                    username=username_base,
                    display_name=display_name,
                    telegram_id=user_tg.id,
                    relationship_score=10,
                )
                session.add(user)
                await session.flush()  # populate user.id

                identity = Identity(
                    user_id=user.id,
                    platform="telegram",
                    platform_id=str(user_tg.id)
                )
                session.add(identity)
                await session.commit()
                await session.refresh(user)
                logger.info("Auto-registered new Telegram user mapping for user_id=%d", user.id)

            # 5. Process through the unified Core Brain orchestration handler
            result = await brain.handle(
                user=user,
                message=message_text,
                source="telegram",
                session=session,
            )

            # 6. Send reply back to Telegram chat
            await update.message.reply_text(result.reply)

        except Exception as exc:
            logger.exception("Error processing message for user %s: %s", user_tg.id, exc)
            await update.message.reply_text(
                "I'm sorry, I encountered an internal problem. Let's try again in a moment! 🌸"
            )

"""
Hinata - Message Handler

Processes incoming text messages through the full AI pipeline:

1. Load/register user profile
2. Store incoming message
3. Retrieve conversation context & memories
4. Determine personality, mood & relationship
5. Build system prompt
6. Call Groq API
7. Clean & validate response
8. Store AI reply
9. Update relationship score
10. Send response to user
"""

from __future__ import annotations

import logging

import telegram

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from ai.context_builder import build_conversation_context
from ai.mood_engine import MoodEngine
from ai.personality_engine import PersonalityEngine
from ai.prompt_builder import PromptBuilder
from ai.relationship_engine import RelationshipEngine
from ai.response_cleaner import clean_response, split_long_message
from memory.memory_manager import get_memories_summary
from services.chat_service import save_message
from services.user_service import get_or_create_user, get_user_preferences

from utils.rate_limit import rate_limiter
from utils.validators import sanitise_input

logger = logging.getLogger(__name__)

_MAINTENANCE_MODE_KEY = "maintenance_mode"


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming text messages through the AI pipeline."""
    user_tg = update.effective_user
    message_text = update.message.text.strip()

    if not message_text:
        return

    logger.info("Message from %s: %.50s...", user_tg.id, message_text)

    # ── Maintenance mode check ────────────────────────────────────
    if context.bot_data.get(_MAINTENANCE_MODE_KEY, False):
        from config import settings
        if user_tg.id != settings.OWNER_ID:
            await update.message.reply_text(
                "🌸 Hinata is taking a short break for maintenance. "
                "I'll be back soon!",
            )
            return

    # ── Rate limiter ──────────────────────────────────────────────
    limiter = context.bot_data.get("rate_limiter", rate_limiter)
    if limiter.is_limited(user_tg.id):
        logger.info("Rate-limited user %s.", user_tg.id)
        return  # Silent drop to avoid spamming

    # ── Sanitise input ────────────────────────────────────────────
    message_text = sanitise_input(message_text)

    # Show typing indicator immediately
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    # ── Shared resources ──────────────────────────────────────────
    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    personality_engine: PersonalityEngine = context.bot_data["personality_engine"]
    mood_engine: MoodEngine = context.bot_data["mood_engine"]
    relationship_engine: RelationshipEngine = context.bot_data["relationship_engine"]
    prompt_builder: PromptBuilder = context.bot_data["prompt_builder"]
    ai_client = context.bot_data.get("ai_client", context.bot_data.get("groq_client"))

    async with session_factory() as session:
        try:
            # 1. Load or create user profile
            user = await get_or_create_user(
                session,
                telegram_id=user_tg.id,
                username=user_tg.username,
                display_name=user_tg.first_name,
            )

            # 2. Save user message
            await save_message(session, user.id, "user", message_text)

            # 3. Retrieve conversation context
            conversation_context = await build_conversation_context(session, user.id)

            # 4. Retrieve memories
            memories_summary = await get_memories_summary(session, user.id)

            # 5. Retrieve preferences
            prefs = await get_user_preferences(session, user.id)
            preferences_text = _format_preferences(prefs)

            # 6. Determine personality
            personality = personality_engine.get_personality(user.current_personality)
            personality_instructions = personality_engine.get_instructions(user.current_personality)

            # 7. Determine mood
            mood = mood_engine.determine_mood(
                current_mood=user.current_mood,
                relationship_score=user.relationship_score,
            )
            mood_instructions = mood_engine.get_instructions(mood)

            # 8. Determine relationship level
            rel_level = relationship_engine.get_level(user.relationship_score)
            rel_instructions = relationship_engine.get_instructions(user.relationship_score)

            # 9. Build system prompt
            system_prompt = prompt_builder.build_system_prompt(
                personality_name=user.current_personality.capitalize(),
                personality=personality,
                mood_name=mood.name,
                mood=mood,
                relationship_level=rel_level,
                relationship_instructions=rel_instructions,
                user_name=user.display_name or user_tg.first_name or "User",
                language=user.language,
                preferences=preferences_text,
                memories=memories_summary,
                personality_instructions=personality_instructions,
                mood_instructions=mood_instructions,
            )

            # 10. Build messages & call AI completion engine
            messages = prompt_builder.build_messages(
                system_prompt,
                conversation_context,
                message_text,
            )

            ai_response = await ai_client.chat_completion(messages)

            # 11. Clean response
            cleaned = clean_response(ai_response)

            # 12. Save AI response
            await save_message(session, user.id, "assistant", cleaned)

            # 13. Update relationship score
            increase = relationship_engine.calculate_score_increase(
                len(message_text),
                user.relationship_score,
            )
            user.relationship_score += increase
            user.current_mood = mood.name
            await session.commit()

            # 14. Send reply
            await _send_reply(update, cleaned)

        except Exception:
            logger.exception("Error processing message from %s.", user_tg.id)
            await update.message.reply_text(
                "Oops... I couldn't think of a reply just now. "
                "Could you try again in a moment? 🌸",
            )


# ── Internal helpers ─────────────────────────────────────────────────────


async def _send_reply(update: Update, text: str) -> None:
    """Send a reply, splitting into multiple messages if needed.

    Falls back to plain text if Markdown parsing fails.
    """
    chunks = split_long_message(text)
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except telegram.error.BadRequest:
            # Malformed Markdown — retry without parsing
            try:
                await update.message.reply_text(chunk)
            except Exception as exc:
                logger.warning("Failed to send reply: %s", exc)


def _format_preferences(prefs) -> str:
    """Format a user's preferences object into a readable string."""
    if prefs is None:
        return "No custom preferences."

    lines: list[str] = []
    mapping = {
        "emoji_level": "Emoji level",
        "reply_length": "Reply length",
        "default_personality": "Default personality",
        "language": "Language",
        "memory_enabled": "Memory enabled",
    }
    for attr, label in mapping.items():
        value = getattr(prefs, attr, None)
        if value is not None:
            lines.append(f"- {label}: {value}")

    return "\n".join(lines) if lines else "No custom preferences."

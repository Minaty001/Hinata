"""
Hinata - Command Handlers

Processes all bot commands (/start, /help, /about, /ping, /settings,
/reset, /forget, /memory, /mood, /personality, /version).
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from constants import (
    AVAILABLE_MOODS,
    AVAILABLE_PERSONALITIES,
    BOT_DESCRIPTION,
    BOT_NAME,
    BOT_VERSION,
)
from memory.memory_manager import (
    forget_all_memories,
    get_memories,
    get_memories_summary,
)
from services.chat_service import clear_conversation_history, get_conversation_count
from services.user_service import get_or_create_user, get_user_preferences, update_user_preferences

logger = logging.getLogger(__name__)


# ── Basic Commands ───────────────────────────────────────────────────────


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — welcome message."""
    user = update.effective_user
    logger.info("User %s (%s) started the bot.", user.id, user.username)

    await update.message.reply_text(
        f"🌸 Hello, {user.first_name}!\n\n"
        f"I'm {BOT_NAME}, your intelligent AI companion. "
        "I'm here to chat, help, and keep you company.\n\n"
        "Try /help to see what I can do.",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — list all commands."""
    help_text = (
        f"🌸 **{BOT_NAME} Help**\n\n"
        "**Chat**\n"
        "Just send me a message! I'll remember our conversations.\n\n"
        "**Commands**\n"
        "/start - Start the bot\n"
        "/help - Show this help\n"
        "/about - About me\n"
        "/ping - Check if I'm alive\n"
        "/settings - View your settings\n"
        "/personality - Change my personality\n"
        "/mood - Change my mood\n"
        "/memory - View saved memories\n"
        "/forget - Forget memories\n"
        "/reset - Reset conversation\n"
        "/version - Version info\n\n"
        "Let's chat! 😊"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /about — show bot information."""
    about_text = (
        f"🌸 **About {BOT_NAME}**\n\n"
        f"{BOT_DESCRIPTION}\n\n"
        "**Features**\n"
        "✨ Natural conversations\n"
        "🧠 Long-term memory\n"
        "🎭 8 personalities\n"
        "💖 Mood & relationship engine\n"
        "📚 Remembers your preferences\n\n"
        f"Version: {BOT_VERSION}\n\n"
        "Built with ❤️ using Python & Groq AI"
    )
    await update.message.reply_text(about_text, parse_mode="Markdown")


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /ping — health check."""
    await update.message.reply_text("🏓 Pong! I'm here and ready to chat!")


async def version_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /version — show version details."""
    import sys
    from config import settings

    lines = [
        f"🤖 **{BOT_NAME}** v{BOT_VERSION}",
        "",
        f"Python: {sys.version.split()[0]}",
        f"Database: SQLite",
        f"AI: Groq API",
        f"Language: {settings.DEFAULT_LANGUAGE}",
        f"Timezone: {settings.TIMEZONE}",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── Settings ─────────────────────────────────────────────────────────────


async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settings — show current user settings."""
    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    async with session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            display_name=update.effective_user.first_name,
        )
        prefs = await get_user_preferences(session, user.id)

    rel_engine = context.bot_data["relationship_engine"]
    rel_level = rel_engine.get_level(user.relationship_score)
    lines = [
        f"⚙️ **Your Settings**",
        "",
        f"**Personality:** {user.current_personality.capitalize()}",
        f"**Mood:** {user.current_mood.capitalize()}",
        f"**Relationship:** {rel_level.replace('_', ' ').title()} "
        f"(score: {user.relationship_score})",
        f"**Language:** {user.language}",
        "",
    ]

    if prefs:
        lines.append(f"**Emoji level:** {prefs.emoji_level}")
        lines.append(f"**Reply length:** {prefs.reply_length}")
        lines.append(f"**Default personality:** {prefs.default_personality.capitalize()}")
        lines.append(f"**Memory enabled:** {'Yes' if prefs.memory_enabled else 'No'}")

    lines.append("")
    lines.append("To change settings, use /personality or /mood.")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── Personality ──────────────────────────────────────────────────────────


async def personality_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /personality — view or change personality.

    Usage: ``/personality`` (lists options) or ``/personality <name>`` (sets).
    """
    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    async with session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            display_name=update.effective_user.first_name,
        )

        if context.args:
            requested = context.args[0].lower()
            if requested in AVAILABLE_PERSONALITIES:
                user.current_personality = requested
                await session.commit()
                await update.message.reply_text(
                    f"🌸 Personality changed to **{requested.capitalize()}**!",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    f"Personality '{requested}' not found. Available: "
                    f"{', '.join(p.capitalize() for p in AVAILABLE_PERSONALITIES)}",
                )
        else:
            current = user.current_personality.capitalize()
            await update.message.reply_text(
                f"🎭 Current personality: **{current}**\n\n"
                f"To change, type:\n"
                f"`/personality <name>`\n\n"
                f"Available: {', '.join(p.capitalize() for p in AVAILABLE_PERSONALITIES)}",
                parse_mode="Markdown",
            )


# ── Mood ─────────────────────────────────────────────────────────────────


async def mood_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /mood — view or change mood.

    Usage: ``/mood`` (shows current) or ``/mood <name>`` (sets).
    """
    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    async with session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            display_name=update.effective_user.first_name,
        )

        if context.args:
            requested = context.args[0].lower()
            if requested in AVAILABLE_MOODS:
                user.current_mood = requested
                await session.commit()
                await update.message.reply_text(
                    f"💖 Mood changed to **{requested.capitalize()}**!",
                    parse_mode="Markdown",
                )
            else:
                await update.message.reply_text(
                    f"Mood '{requested}' not found. Available: "
                    f"{', '.join(m.capitalize() for m in AVAILABLE_MOODS)}",
                )
        else:
            await update.message.reply_text(
                f"💖 Current mood: **{user.current_mood.capitalize()}**\n\n"
                f"To change, type:\n"
                f"`/mood <name>`\n\n"
                f"Available: {', '.join(m.capitalize() for m in AVAILABLE_MOODS)}\n\n"
                f"_(Mood also changes naturally over time!)_",
                parse_mode="Markdown",
            )


# ── Memory ───────────────────────────────────────────────────────────────


async def memory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /memory — view saved memories."""
    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    async with session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            display_name=update.effective_user.first_name,
        )
        memories = await get_memories(session, user.id)

    if not memories:
        await update.message.reply_text(
            "🧠 I don't have any special memories saved yet. "
            "Tell me something about yourself and I'll remember it!",
        )
        return

    lines = ["🧠 **Your Memories**", ""]
    for mem in memories:
        icon = {"fact": "📌", "preference": "❤️", "goal": "🎯", "event": "📅",
                "achievement": "🏆", "nickname": "💫", "session": "💭"}.get(mem.type, "📝")
        importance = "⭐" * mem.importance
        lines.append(f"{icon} *[{mem.type}]* {mem.content} {importance}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def forget_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /forget — forget memories.

    Usage: ``/forget`` — forget everything, ``/forget <type>`` — forget by type.
    """
    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    async with session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            display_name=update.effective_user.first_name,
        )

        if context.args:
            # Forget by type
            forget_type = context.args[0].lower()
            memories = await get_memories(session, user.id, type=forget_type)
            count = 0
            for mem in memories:
                mem.is_active = False
                count += 1
            if count:
                await session.commit()
                await update.message.reply_text(
                    f"Forgot {count} {'memories' if count != 1 else 'memory'} "
                    f"of type '{forget_type}'. 🧹",
                )
            else:
                await update.message.reply_text(
                    f"No memories of type '{forget_type}' found.",
                )
        else:
            # Forget all
            count = await forget_all_memories(session, user.id)
            await update.message.reply_text(
                f"Forgot all {count} memories. 🧹\n\n"
                "_I'll remember new things as we chat._",
                parse_mode="Markdown",
            )


# ── Reset ────────────────────────────────────────────────────────────────


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reset — reset conversation, relationship, and mood.

    This clears the conversation history, resets the relationship
    score to zero, and resets the mood to the default.
    """
    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    async with session_factory() as session:
        user = await get_or_create_user(
            session,
            telegram_id=update.effective_user.id,
            username=update.effective_user.username,
            display_name=update.effective_user.first_name,
        )

        # Clear conversation history
        cleared = await clear_conversation_history(session, user.id)

        # Reset relationship
        user.relationship_score = 0
        user.current_mood = "happy"

        # Forget all memories
        forgotten = await forget_all_memories(session, user.id)

        await session.commit()

    await update.message.reply_text(
        f"🔄 Reset complete!\n\n"
        f"- Cleared {cleared} messages\n"
        f"- Forgotten {forgotten} memories\n"
        f"- Relationship reset\n"
        f"- Mood reset to Happy\n\n"
        f"Let's start fresh! 🌸",
    )

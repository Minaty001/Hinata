"""
Hinata - Telegram Bot Setup

Configures the Telegram bot application, registers all handlers,
and manages the bot lifecycle.
"""

from __future__ import annotations

import logging

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from ai.mood_engine import MoodEngine
from ai.personality_engine import PersonalityEngine
from ai.relationship_engine import RelationshipEngine
from config import settings
from database.database import async_session_factory
from handlers.admin_handler import admin_command
from handlers.command_handler import (
    about_command,
    forget_command,
    help_command,
    memory_command,
    mood_command,
    personality_command,
    ping_command,
    reset_command,
    settings_command,
    start_command,
    version_command,
)
from handlers.message_handler import handle_message
from handlers.error_handler import error_handler
from utils.rate_limit import rate_limiter

logger = logging.getLogger(__name__)


def create_application() -> Application:
    """Create and configure the Telegram bot application.

    Injects shared resources (DB session factory, engines, rate limiter)
    into ``bot_data`` so handlers can access them without creating
    new instances on every request.

    Returns:
        Fully configured Application instance with all handlers registered.
    """
    application: Application = (
        ApplicationBuilder()
        .token(settings.BOT_TOKEN)
        .build()
    )

    # ── Shared Resources ───────────────────────────────────────────
    application.bot_data["session_factory"] = async_session_factory
    application.bot_data["personality_engine"] = PersonalityEngine()
    application.bot_data["mood_engine"] = MoodEngine()
    application.bot_data["relationship_engine"] = RelationshipEngine()
    application.bot_data["rate_limiter"] = rate_limiter

    # ── Command Handlers ──────────────────────────────────────────
    # User commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("version", version_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CommandHandler("personality", personality_command))
    application.add_handler(CommandHandler("mood", mood_command))
    application.add_handler(CommandHandler("memory", memory_command))
    application.add_handler(CommandHandler("forget", forget_command))
    application.add_handler(CommandHandler("reset", reset_command))

    # Admin commands
    application.add_handler(CommandHandler("admin", admin_command))

    # ── Message Handlers ──────────────────────────────────────────
    # Catch all text messages except commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ── Error Handler ─────────────────────────────────────────────
    application.add_error_handler(error_handler)

    logger.info(
        "Bot application configured with %d command handlers.",
        len(application.handlers.get(0, [])),
    )
    return application

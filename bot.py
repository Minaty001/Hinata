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

from config import settings
from handlers.command_handler import (
    about_command,
    help_command,
    ping_command,
    start_command,
)
from handlers.message_handler import handle_message
from handlers.error_handler import error_handler

logger = logging.getLogger(__name__)


def create_application() -> Application:
    """Create and configure the Telegram bot application.

    Returns:
        Fully configured Application instance with all handlers registered.
    """
    application: Application = (
        ApplicationBuilder()
        .token(settings.BOT_TOKEN)
        .build()
    )

    # ── Command Handlers ──────────────────────────────────────────
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("ping", ping_command))

    # ── Message Handlers ──────────────────────────────────────────
    # Catch all text messages except commands
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ── Error Handler ─────────────────────────────────────────────
    application.add_error_handler(error_handler)

    logger.info("Bot application configured with all handlers.")
    return application

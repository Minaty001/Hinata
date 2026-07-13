"""
Hinata - Error Handler

Global error handler for the Telegram bot.
Logs errors and sends friendly messages to users when something goes wrong.
"""

from __future__ import annotations

import logging
import traceback

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def error_handler(update: Update | None, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors raised by the bot.

    Logs the full error traceback and notifies the user if possible.
    """
    logger.error("Exception while handling an update: %s", context.error)
    logger.error(traceback.format_exc())

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Oops... I ran into a little trouble there. 🌸\n"
            "Could you try again in a moment?",
        )

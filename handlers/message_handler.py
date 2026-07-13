"""
Hinata - Message Handler

Handles incoming text messages from users.
Routes messages through the AI pipeline for processing.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming text messages.

    This is the main entry point for user messages. In future phases,
    this will route through the full AI pipeline (memory → mood →
    personality → prompt → Groq → response).

    Currently sends a placeholder response acknowledging receipt.
    """
    user = update.effective_user
    message_text = update.message.text.strip()

    if not message_text:
        return

    logger.info("Message from %s: %.50s...", user.id, message_text)

    # Show typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    # Placeholder: Phase 1 stub — will be replaced by AI pipeline
    await update.message.reply_text(
        f"You said: _{message_text}_\n\n"
        "_(I'm still learning! My AI brain will be connected soon.)_",
        parse_mode="Markdown",
    )

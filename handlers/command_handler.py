"""
Hinata - Command Handlers

Processes all bot commands (/start, /help, /about, /ping, etc.).
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from constants import BOT_DESCRIPTION, BOT_NAME, BOT_VERSION

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command.

    Sends a welcome message to new users.
    """
    user = update.effective_user
    logger.info("User %s (%s) started the bot.", user.id, user.username)

    await update.message.reply_text(
        f"🌸 Hello, {user.first_name}!\n\n"
        f"I'm {BOT_NAME}, your intelligent AI companion. "
        "I'm here to chat, help, and keep you company.\n\n"
        "Try /help to see what I can do.",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command.

    Lists all available commands and their descriptions.
    """
    help_text = (
        f"🌸 **{BOT_NAME} Help**\n\n"
        "Here's what I can do:\n\n"
        "**Commands**\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/about - About Hinata\n"
        "/ping - Check if I'm alive\n"
        "/settings - View your settings\n"
        "/reset - Reset your chat history\n"
        "/forget - Forget specific memories\n"
        "/memory - View your memories\n"
        "/mood - Check my current mood\n"
        "/personality - Change my personality\n"
        "/version - Version info\n\n"
        "Just send me a message and we can chat! 😊"
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /about command.

    Shows information about Hinata.
    """
    about_text = (
        f"🌸 **About {BOT_NAME}**\n\n"
        f"{BOT_DESCRIPTION}\n\n"
        "**Features**\n"
        "✨ Natural conversations\n"
        "🧠 Long-term memory\n"
        "🎭 Multiple personalities\n"
        "💖 Mood & relationship engine\n"
        "📚 Remembers your preferences\n\n"
        f"Version: {BOT_VERSION}\n\n"
        "Built with ❤️ using Python & Groq AI"
    )

    await update.message.reply_text(about_text, parse_mode="Markdown")


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /ping command.

    Simple health check to verify the bot is responsive.
    """
    await update.message.reply_text("🏓 Pong! I'm here!")

"""
Hinata Hyuga - Telegram Bot Entry Point (bot.py)

Configures the Telegram bot application, registers handlers,
initializes database, and manages the Telegram bot lifecycle.

Usage:
    python bot.py
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from ai.mood_engine import MoodEngine
from ai.personality_engine import PersonalityEngine
from ai.prompt_builder import PromptBuilder
from ai.relationship_engine import RelationshipEngine
from ai.unified_ai_client import UnifiedAIClient
from ai.feeling_detector import FeelingDetector
from ai.need_analyzer import NeedAnalyzer
from ai.defense_detector import DefenseDetector
from ai.response_mode_selector import ResponseModeSelector
from config import settings
from constants import BOT_VERSION, LOGS_DIR
from database.database import async_session_factory, close_database, init_database
from handlers.admin_handler import admin_command
from handlers.command_handler import (
    about_command,
    forget_command,
    help_command,
    memory_command,
    mood_command,
    personality_command,
    ping_command,
    provider_command,
    reset_command,
    settings_command,
    start_command,
    version_command,
)
from handlers.error_handler import error_handler
from handlers.message_handler import handle_message
from training.behavioral_tracker import BehavioralTracker
from training.quality_scorer import QualityScorer
from training.conversation_encoder import ConversationEncoder
from training.model_router import ModelRouter
from utils.rate_limit import rate_limiter

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Configure logging for the Telegram bot."""
    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / "hinata_bot.log"

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def create_application() -> Application:
    """Create and configure the Telegram bot application."""
    application: Application = (
        ApplicationBuilder()
        .token(settings.BOT_TOKEN)
        .build()
    )

    # Shared Resources
    application.bot_data["session_factory"] = async_session_factory
    application.bot_data["personality_engine"] = PersonalityEngine()
    application.bot_data["mood_engine"] = MoodEngine()
    application.bot_data["relationship_engine"] = RelationshipEngine()
    application.bot_data["rate_limiter"] = rate_limiter
    application.bot_data["prompt_builder"] = PromptBuilder()

    # Next-Level AI Engines
    application.bot_data["feeling_detector"] = FeelingDetector()
    application.bot_data["need_analyzer"] = NeedAnalyzer()
    application.bot_data["defense_detector"] = DefenseDetector()
    application.bot_data["response_selector"] = ResponseModeSelector()
    application.bot_data["behavioral_tracker"] = BehavioralTracker()
    application.bot_data["quality_scorer"] = QualityScorer()
    application.bot_data["conversation_encoder"] = ConversationEncoder()
    application.bot_data["model_router"] = ModelRouter()

    ai_client = UnifiedAIClient()
    application.bot_data["ai_client"] = ai_client

    # Command Handlers
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
    application.add_handler(CommandHandler("provider", provider_command))

    # Admin Handler
    application.add_handler(CommandHandler("admin", admin_command))

    # Message Handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error Handler
    application.add_error_handler(error_handler)

    logger.info("Bot application configured with %d command handlers.", len(application.handlers.get(0, [])))
    return application


async def main() -> None:
    """Telegram bot main entry point."""
    setup_logging()
    logger.info("Starting Hinata Hyuga Telegram Bot v%s...", BOT_VERSION)

    import database.models  # noqa: F401
    await init_database()

    application = create_application()
    await application.initialize()
    await application.updater.start_polling(
        allowed_updates=["message", "callback_query"],
        drop_pending_updates=True,
    )
    await application.start()
    logger.info("Hinata Hyuga Telegram Bot is running.")

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Shutdown signal received.")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            pass

    try:
        await stop_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down bot...")
        await application.stop()
        await application.updater.stop()
        await application.shutdown()
        await close_database()
        logger.info("Hinata Hyuga Telegram Bot stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested.")
        sys.exit(0)
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        sys.exit(1)

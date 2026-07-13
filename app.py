"""
Hinata - Application Entry Point

Starts the Telegram bot, initializes the database, and manages
the application lifecycle.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

from config import settings
from constants import LOGS_DIR

# ── Logging Setup ─────────────────────────────────────────────────────────

def setup_logging() -> None:
    """Configure logging to both file and console."""
    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / "hinata.log"

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


# ── Main ──────────────────────────────────────────────────────────────────

async def main() -> None:
    """Application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    from constants import BOT_VERSION
    logger.info("Starting Hinata v%s...", BOT_VERSION)
    logger.info("Log level: %s", settings.LOG_LEVEL)

    # Initialize database
    from database.database import init_database, close_database

    await init_database()

    # Create and start bot
    from bot import create_application

    application = create_application()

    logger.info("Hinata is now running.")
    try:
        await application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
    finally:
        await close_database()
        logger.info("Hinata stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested.")
        sys.exit(0)
    except Exception as exc:
        print(f"Fatal error: {exc}", file=sys.stderr)
        sys.exit(1)

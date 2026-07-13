"""
Hinata - Admin Handler

Owner-only administrative commands for managing the bot.
All commands check that the sender's Telegram ID matches the
configured OWNER_ID before executing.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

from config import settings
from constants import BOT_VERSION, DATA_DIR, LOGS_DIR
from database.models import Memory, User
from utils.formatter import bold, bullet_list, code, code_block, key_value, timestamp
from utils.validators import is_owner

logger = logging.getLogger(__name__)

_MAINTENANCE_MODE_KEY = "maintenance_mode"


# ── Owner Guard ──────────────────────────────────────────────────────────


async def _require_owner(update: Update) -> bool:
    """Check if the sender is the bot owner. Sends a denial message if not.

    Returns:
        True if the user is authorised.
    """
    if not update.effective_user:
        return False
    if is_owner(update.effective_user.id, settings.OWNER_ID):
        return True
    await update.message.reply_text("You don't have permission to use this command.")
    return False


# ── Admin Commands ───────────────────────────────────────────────────────


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics — user counts, message counts, uptime."""
    if not await _require_owner(update):
        return

    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    async with session_factory() as session:
        # User counts
        total_users = await session.scalar(select(func.count(User.id)))
        active_users = await session.scalar(
            select(func.count(User.id)).where(User.is_active.is_(True))
        )

        # Memory count
        total_memories = await session.scalar(select(func.count(Memory.id)))

        # Total relationship score sum (rough engagement metric)
        score_sum = await session.scalar(select(func.sum(User.relationship_score))) or 0

    # Build stats message
    lines = [
        bold("📊 Bot Statistics"),
        "",
        key_value("Version", BOT_VERSION),
        key_value("Total Users", str(total_users or 0)),
        key_value("Active Users", str(active_users or 0)),
        key_value("Total Memories", str(total_memories or 0)),
        key_value("Total Engagement Score", str(int(score_sum))),
        "",
        bold("System"),
        key_value("Python", os.sys.version.split()[0]),
        key_value("Time", timestamp()),
    ]

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Broadcast a message to all active users.

    Usage: ``/admin broadcast <message>``
    """
    if not await _require_owner(update):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: `/admin broadcast <message>`",
            parse_mode="Markdown",
        )
        return

    message = " ".join(context.args)
    logger.info("Admin broadcast: %.100s", message)

    # For now, log the broadcast. Full fan-out requires user chat ID storage.
    await update.message.reply_text(
        f"📢 Broadcast queued:\n\n{message}\n\n"
        f"_(Full fan-out requires user chat ID tracking — logged for now.)_",
        parse_mode="Markdown",
    )


async def admin_maintenance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle maintenance mode on/off.

    When enabled, the bot replies to non-owner messages with a
    maintenance notice.
    """
    if not await _require_owner(update):
        return

    current = context.bot_data.get(_MAINTENANCE_MODE_KEY, False)
    context.bot_data[_MAINTENANCE_MODE_KEY] = not current

    status = "enabled" if not current else "disabled"
    await update.message.reply_text(f"🛠 Maintenance mode {status}.")
    logger.info("Maintenance mode %s by owner.", status)


async def admin_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the last N lines of the bot log.

    Usage: ``/admin logs [lines=20]``
    """
    if not await _require_owner(update):
        return

    try:
        n = int(context.args[0]) if context.args else 20
        n = min(max(n, 5), 100)
    except (IndexError, ValueError):
        n = 20

    log_file = LOGS_DIR / "hinata.log"
    if not log_file.exists():
        await update.message.reply_text("No log file found.")
        return

    try:
        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()
        tail = "".join(lines[-n:])
        if not tail.strip():
            await update.message.reply_text("Log is empty.")
            return
        # Truncate if too long for Telegram
        if len(tail) > 3500:
            tail = tail[-3500:]
        await update.message.reply_text(
            f"{bold('Recent Logs')} (last {n} lines):\n\n{code_block(tail)}",
            parse_mode="Markdown",
        )
    except Exception as exc:
        await update.message.reply_text(f"Failed to read logs: {exc}")


async def admin_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a backup of the SQLite database.

    Copies the current database file to the backups directory
    with a timestamp.
    """
    if not await _require_owner(update):
        return

    from database.backup import create_backup

    try:
        backup_path = await create_backup()
        await update.message.reply_text(
            f"✅ Database backup created:\n{code(str(backup_path))}",
            parse_mode="Markdown",
        )
    except Exception as exc:
        await update.message.reply_text(f"❌ Backup failed: {exc}")


async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show a summary of active users."""
    if not await _require_owner(update):
        return

    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    async with session_factory() as session:
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.last_interaction.desc())
            .limit(10)
        )
        result = await session.execute(stmt)
        users = result.scalars().all()

    if not users:
        await update.message.reply_text("No active users.")
        return

    lines = [bold("👤 Active Users (top 10)"), ""]
    for u in users:
        last_seen = u.last_interaction.strftime("%Y-%m-%d %H:%M")
        name = u.display_name or u.username or f"tg:{u.telegram_id}"
        lines.append(f"• {name} — score: {u.relationship_score} — last: {last_seen}")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available admin commands."""
    if not await _require_owner(update):
        return

    commands = bullet_list([
        "/admin stats — Bot statistics",
        "/admin users — Active users",
        "/admin logs [N] — Recent log lines",
        "/admin broadcast <msg> — Broadcast message",
        "/admin maintenance — Toggle maintenance mode",
        "/admin backup — Backup database",
    ])

    text = f"{bold('🛠 Admin Commands')}\n\n{commands}"
    await update.message.reply_text(text, parse_mode="Markdown")


# ── Router ───────────────────────────────────────────────────────────────


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route /admin to the appropriate sub-handler based on the first argument.

    Usage: ``/admin stats``, ``/admin broadcast <msg>``, etc.
    """
    subcommands = {
        "stats": admin_stats,
        "users": admin_users,
        "logs": admin_logs,
        "broadcast": admin_broadcast,
        "maintenance": admin_maintenance,
        "backup": admin_backup,
        "help": admin_help,
    }

    if not context.args:
        await admin_help(update, context)
        return

    subcommand = context.args[0].lower()
    handler = subcommands.get(subcommand)

    if handler:
        # Remove the subcommand name from args so the handler gets the rest
        context.args = context.args[1:]
        await handler(update, context)
    else:
        await update.message.reply_text(
            f"Unknown admin command: `{subcommand}`. Use `/admin help` for available commands.",
            parse_mode="Markdown",
        )

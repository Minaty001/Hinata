"""
Hinata - Database Backup

Utilities for backing up and restoring the SQLite database.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from config import settings
from constants import BACKUPS_DIR

logger = logging.getLogger(__name__)


def _resolve_db_path() -> Path:
    """Resolve the database file path from the DATABASE_URL."""
    db_url = settings.DATABASE_URL
    if "///" not in db_url:
        raise RuntimeError(f"Cannot parse database URL: {db_url}")
    db_path_str = db_url.split("///", 1)[1]
    db_path = Path(db_path_str)
    if not db_path.is_absolute():
        from constants import PROJECT_ROOT
        db_path = PROJECT_ROOT / db_path
    return db_path


async def create_backup() -> Path:
    """Create a timestamped copy of the SQLite database.

    Returns:
        Path to the backup file.

    Raises:
        FileNotFoundError: If the source database file doesn't exist.
        RuntimeError: If the backup fails.
    """
    BACKUPS_DIR.mkdir(exist_ok=True)
    db_path = _resolve_db_path()

    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"hinata_backup_{timestamp}.db"
    backup_path = BACKUPS_DIR / backup_name

    try:
        shutil.copy2(db_path, backup_path)
        logger.info("Database backup created: %s", backup_path)
        return backup_path
    except OSError as exc:
        raise RuntimeError(f"Backup failed: {exc}") from exc

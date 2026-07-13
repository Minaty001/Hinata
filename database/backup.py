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


async def create_backup() -> Path:
    """Create a timestamped copy of the SQLite database.

    Returns:
        Path to the backup file.

    Raises:
        FileNotFoundError: If the source database file doesn't exist.
        RuntimeError: If the backup fails.
    """
    BACKUPS_DIR.mkdir(exist_ok=True)

    # Extract the file path from the SQLAlchemy URL
    # sqlite+aiosqlite:///data/hinata.db → data/hinata.db
    db_url = settings.DATABASE_URL
    if "///" not in db_url:
        raise RuntimeError(f"Cannot parse database URL: {db_url}")

    db_path_str = db_url.split("///", 1)[1]
    db_path = Path(db_path_str)

    if not db_path.is_absolute():
        from constants import PROJECT_ROOT
        db_path = PROJECT_ROOT / db_path

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


async def list_backups() -> list[dict[str, object]]:
    """List available backups sorted by creation time (newest first).

    Returns:
        List of dicts with ``path``, ``name``, ``size``, and ``modified`` keys.
    """
    if not BACKUPS_DIR.exists():
        return []

    backups: list[dict[str, object]] = []
    for f in sorted(BACKUPS_DIR.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if f.suffix == ".db" and f.name.startswith("hinata_backup_"):
            stat = f.stat()
            backups.append({
                "path": f,
                "name": f.name,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            })
    return backups


async def restore_backup(backup_name: str) -> Path:
    """Restore a backup by name.

    Args:
        backup_name: The backup filename (e.g. ``hinata_backup_20260713_120000.db``).

    Returns:
        Path to the restored database.

    Raises:
        FileNotFoundError: If the backup doesn't exist.
    """
    backup_path = BACKUPS_DIR / backup_name
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup not found: {backup_path}")

    db_url = settings.DATABASE_URL
    db_path_str = db_url.split("///", 1)[1]
    db_path = Path(db_path_str)

    if not db_path.is_absolute():
        from constants import PROJECT_ROOT
        db_path = PROJECT_ROOT / db_path

    shutil.copy2(backup_path, db_path)
    logger.info("Database restored from backup: %s", backup_name)
    return db_path

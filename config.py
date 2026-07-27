"""
Hinata - Configuration Module

Loads and validates all configuration from environment variables.
Uses Pydantic v1 BaseSettings for type-safe configuration management.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from dotenv import load_dotenv
from pydantic import BaseSettings


# Load .env file from project root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

import os


def _resolve_db_url(url: str | None) -> str:
    """Resolve the database URL to an absolute path if it's relative."""
    if not url:
        url = "sqlite+aiosqlite:///data/hinata.db"
    if url.startswith("sqlite+aiosqlite:///") and not url.startswith("sqlite+aiosqlite:////"):
        # Relative path — make it absolute
        rel_path = url[len("sqlite+aiosqlite:///"):]
        abs_path = PROJECT_ROOT / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{abs_path}"
    return url


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram
    BOT_TOKEN: str 

    # Groq
    GROQ_API_KEY: str = ""

    # AI Provider & OpenCode Zen (https://opencode.ai/zen/v1)
    AI_PROVIDER: str = "groq"
    OPENCODE_ZEN_BASE_URL: str = "https://opencode.ai/zen/v1"
    OPENCODE_ZEN_API_KEY: str = ""
    OPENCODE_ZEN_MODEL: str = "opencode-zen-free"
    ENABLE_AI_FALLBACK: bool = True

    # Database
    DATABASE_URL: str = ""

    # Owner
    OWNER_ID: int

    # Logging
    LOG_LEVEL: str = "INFO"

    # Defaults
    DEFAULT_LANGUAGE: str = "en"
    TIMEZONE: str = "Asia/Kolkata"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        allow_mutation = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Resolve relative DB path to absolute
        object.__setattr__(self, "DATABASE_URL", _resolve_db_url(self.DATABASE_URL))


# Singleton config instance
settings = Settings()

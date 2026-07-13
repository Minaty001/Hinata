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


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram
    BOT_TOKEN: str

    # Groq
    GROQ_API_KEY: str

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///data/hinata.db"

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


# Singleton config instance
settings = Settings()

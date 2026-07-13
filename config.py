"""
Hinata - Configuration Module

Loads and validates all configuration from environment variables.
Uses pydantic-settings for type-safe configuration management.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


# Load .env file from project root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", frozen=True)

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


# Singleton config instance
settings = Settings()  # type: ignore[call-arg]

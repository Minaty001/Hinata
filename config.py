"""
Hinata - Configuration Module

Loads and validates all configuration from environment variables.
Uses Pydantic v1 BaseSettings for type-safe configuration management.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from dotenv import load_dotenv
try:
    from pydantic_settings import BaseSettings
    from pydantic import field_validator
    _USE_V2 = True
except ImportError:
    from pydantic import BaseSettings, validator  # type: ignore
    _USE_V2 = False


# Load .env file from project root
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

import os


def _resolve_db_url(url: str | None) -> str:
    """Resolve the database URL to an absolute path if it's relative."""
    if not url:
        url = "sqlite:///data/hinata.db"
    # Convert legacy aiosqlite scheme to standard sqlite scheme if present
    if "sqlite+aiosqlite:///" in url:
        url = url.replace("sqlite+aiosqlite:///", "sqlite:///")
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        rel_path = url[len("sqlite:///"):]
        abs_path = PROJECT_ROOT / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{abs_path}"
    return url


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Web Application
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = 2027

    # Telegram
    BOT_TOKEN: str = ""

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
    OWNER_ID: int = 0

    if _USE_V2:
        @field_validator("OWNER_ID", mode="before")
        @classmethod
        def _validate_owner_id_v2(cls, v: Any) -> int:
            if isinstance(v, int):
                return v
            if isinstance(v, str):
                v_clean = v.strip()
                if v_clean.isdigit() or (v_clean.startswith("-") and v_clean[1:].isdigit()):
                    return int(v_clean)
            return 0
    else:
        @validator("OWNER_ID", pre=True)
        def _validate_owner_id_v1(cls, v: Any) -> int:
            if isinstance(v, int):
                return v
            if isinstance(v, str):
                v_clean = v.strip()
                if v_clean.isdigit() or (v_clean.startswith("-") and v_clean[1:].isdigit()):
                    return int(v_clean)
            return 0

    # Logging
    LOG_LEVEL: str = "INFO"

    # Defaults
    DEFAULT_LANGUAGE: str = "hinglish"
    TIMEZONE: str = "Asia/Kolkata"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Resolve relative DB path to absolute
        object.__setattr__(self, "DATABASE_URL", _resolve_db_url(self.DATABASE_URL))


# Singleton config instance
settings = Settings()

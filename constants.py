"""
Hinata - Constants Module

Centralized constants used across the application.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final


# ── Paths ──────────────────────────────────────────────────────────────────

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent
DATA_DIR: Final[Path] = PROJECT_ROOT / "data"
LOGS_DIR: Final[Path] = PROJECT_ROOT / "logs"
BACKUPS_DIR: Final[Path] = PROJECT_ROOT / "backups"
PROMPTS_DIR: Final[Path] = PROJECT_ROOT / "prompts"


# ── Bot Info ───────────────────────────────────────────────────────────────

BOT_NAME: Final[str] = "Hinata"
BOT_VERSION: Final[str] = "0.3.0"
BOT_DESCRIPTION: Final[str] = "Your Intelligent AI Companion"
BOT_TAGLINE: Final[str] = "A warm, intelligent AI companion for Telegram."


# ── Telegram Limits ────────────────────────────────────────────────────────

TELEGRAM_MAX_MESSAGE_LENGTH: Final[int] = 4096
TELEGRAM_MAX_CAPTION_LENGTH: Final[int] = 1024


# ── Personality ────────────────────────────────────────────────────────────

AVAILABLE_PERSONALITIES: Final[list[str]] = [
    "sweet",
    "calm",
    "smart",
    "gamer",
    "playful",
    "curious",
    "boss",
    "supportive",
]

DEFAULT_PERSONALITY: Final[str] = "sweet"


# ── Moods ──────────────────────────────────────────────────────────────────

AVAILABLE_MOODS: Final[list[str]] = [
    "happy",
    "sad",
    "sleepy",
    "excited",
    "curious",
    "relaxed",
    "energetic",
    "shy",
    "thoughtful",
]

DEFAULT_MOOD: Final[str] = "happy"


# ── Relationship Levels ────────────────────────────────────────────────────

RELATIONSHIP_LEVELS: Final[list[str]] = [
    "stranger",
    "acquaintance",
    "friend",
    "close_friend",
    "best_friend",
]

RELATIONSHIP_THRESHOLDS: Final[dict[str, int]] = {
    "stranger": 0,
    "acquaintance": 50,
    "friend": 150,
    "close_friend": 400,
    "best_friend": 800,
}


# ── Memory ─────────────────────────────────────────────────────────────────

MEMORY_TYPES: Final[list[str]] = [
    "fact",
    "preference",
    "goal",
    "event",
    "achievement",
    "relationship",
    "nickname",
    "session",
]


# ── Rate Limiting ──────────────────────────────────────────────────────────

RATE_LIMIT_MESSAGES: Final[int] = 20
RATE_LIMIT_WINDOW: Final[int] = 60  # seconds


# ── Timeouts ───────────────────────────────────────────────────────────────

GROQ_TIMEOUT: Final[int] = 30  # seconds
GROQ_RETRIES: Final[int] = 2
GROQ_RETRY_DELAY: Final[float] = 1.0  # seconds


# ── Groq ───────────────────────────────────────────────────────────────────

GROQ_MODEL: Final[str] = "llama-3.3-70b-versatile"
GROQ_MAX_TOKENS: Final[int] = 50
GROQ_TEMPERATURE: Final[float] = 0.8

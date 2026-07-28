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

BOT_NAME: Final[str] = "Hinata Hyuga"
BOT_CREATOR: Final[str] = "Minaty001"
BOT_GITHUB: Final[str] = "https://github.com/Minaty001/hinata"
BOT_VERSION: Final[str] = "0.3.0"
BOT_DESCRIPTION: Final[str] = "A sweet, warm AI girl companion named Hinata Hyuga, created by Minaty001. Auto-trained and continuously learning from user data."

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
DEFAULT_LANGUAGE: Final[str] = "hinglish"


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



# ── AI Providers ───────────────────────────────────────────────────────────

# ── AI Providers Catalog ───────────────────────────────────────────────────

AVAILABLE_AI_PROVIDERS: Final[list[str]] = [
    "groq",
    "opencode_zen",
    "openai",
    "gemini",
    "openrouter",
    "bytez",
]
DEFAULT_AI_PROVIDER: Final[str] = "groq"

PROVIDER_CATALOG: Final[dict[str, dict]] = {
    "groq": {
        "name": "Groq Cloud API",
        "default_base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ],
    },
    "opencode_zen": {
        "name": "OpenCode Zen API",
        "default_base_url": "https://opencode.ai/zen/v1",
        "default_model": "opencode-zen-free",
        "models": [
            "opencode-zen-free",
            "opencode/big-pickle",
            "opencode/deepseek-v4-flash-free",
            "opencode/nemotron-3-ultra-free",
            "opencode/mimo-v2.5-free",
            "deepseek-r1",
            "qwen2.5-72b-instruct",
        ],
    },
    "openai": {
        "name": "OpenAI API",
        "default_base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "models": [
            "gpt-4o-mini",
            "gpt-4o",
            "o3-mini",
            "gpt-4-turbo",
        ],
    },
    "gemini": {
        "name": "Google Gemini API",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.0-flash",
        "models": [
            "gemini-2.0-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
    },
    "openrouter": {
        "name": "OpenRouter API",
        "default_base_url": "https://openrouter.ai/api/v1",
        "default_model": "meta-llama/llama-3.3-70b-instruct",
        "models": [
            "meta-llama/llama-3.3-70b-instruct",
            "deepseek/deepseek-r1",
            "anthropic/claude-3.5-sonnet",
            "google/gemini-2.0-flash-001",
            "qwen/qwen-2.5-72b-instruct",
        ],
    },
    "bytez": {
        "name": "Bytez API",
        "default_base_url": "https://api.bytez.com/v1",
        "default_model": "bytez-default",
        "models": [
            "bytez-default",
            "Qwen/Qwen2.5-72B-Instruct",
            "meta-llama/Llama-3.3-70B-Instruct",
        ],
    },
}

GROQ_MAX_TOKENS: Final[int] = 50
GROQ_TEMPERATURE: Final[float] = 0.8

OPENCODE_ZEN_FREE_MODELS: Final[list[str]] = PROVIDER_CATALOG["opencode_zen"]["models"]


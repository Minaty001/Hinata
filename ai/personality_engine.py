"""
Hinata - Personality Engine

Loads personality definitions from JSON and provides the active
personality's traits for prompt construction. Each personality
defines tone, humor, vocabulary, emoji usage, and energy level.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from constants import PROMPTS_DIR

logger = logging.getLogger(__name__)

_PERSONALITIES_PATH: Path = PROMPTS_DIR / "personalities.json"


class PersonalityEngine:
    """Manages personality loading and trait access."""

    def __init__(self) -> None:
        self._personalities: dict[str, dict[str, Any]] = {}
        self._load_personalities()

    # ── Public API ─────────────────────────────────────────────────

    def get_personality(self, name: str) -> dict[str, Any]:
        """Return the trait dict for a named personality.

        Falls back to 'sweet' if the requested personality doesn't exist.
        """
        key = name.lower()
        if key in self._personalities:
            return dict(self._personalities[key])
        logger.warning("Personality '%s' not found, falling back to 'sweet'.", name)
        return dict(self._personalities.get("sweet", {}))

    def get_instructions(self, name: str) -> str:
        """Build instruction text for a personality to insert into the prompt."""
        p = self.get_personality(name)
        parts = [
            f"You are currently in '{p.get('name', name)}' personality mode.",
            f"Tone: {p.get('tone', 'warm and friendly')}.",
            f"Humor level: {p.get('humor_level', 'moderate')}.",
            f"Energy level: {p.get('energy_level', 'moderate')}.",
        ]
        return " ".join(parts)

    def list_personalities(self) -> list[str]:
        """Return sorted list of available personality names."""
        return sorted(self._personalities.keys())

    # ── Internal ───────────────────────────────────────────────────

    def _load_personalities(self) -> None:
        """Load personality definitions from the JSON file."""
        try:
            with open(_PERSONALITIES_PATH, encoding="utf-8") as f:
                self._personalities = json.load(f)
            logger.info(
                "Loaded %d personalities.", len(self._personalities)
            )
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.error("Failed to load personalities: %s", exc)
            self._personalities = {
                "sweet": {
                    "name": "Sweet",
                    "tone": "warm and affectionate",
                    "humor_level": "moderate",
                    "emoji_frequency": "normal",
                    "vocabulary": [],
                    "greeting_style": "soft and welcoming",
                    "energy_level": "moderate",
                    "reply_length": "normal",
                }
            }

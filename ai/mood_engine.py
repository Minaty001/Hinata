"""
Hinata - Mood Engine

Manages Hinata's dynamic emotional state. Mood is determined by
conversation sentiment, time of day, random variation, and
relationship level. Mood affects word choice, emoji usage, energy,
and conversation style.
"""

from __future__ import annotations

import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from constants import PROMPTS_DIR

logger = logging.getLogger(__name__)

_MOODS_PATH: Path = PROMPTS_DIR / "moods.json"


@dataclass
class MoodState:
    """The current mood state and its modifiers."""

    name: str = "happy"
    energy_modifier: float = 1.0
    tone_modifier: str = "cheerful and bright"
    description: str = "Bright, cheerful, and positive."


class MoodEngine:
    """Determines and manages Hinata's current mood."""

    def __init__(self) -> None:
        self._moods: dict[str, dict[str, Any]] = {}
        self._load_moods()

    # ── Public API ─────────────────────────────────────────────────

    def determine_mood(
        self,
        *,
        current_mood: str | None = None,
        relationship_score: int = 0,
        hour: int | None = None,
    ) -> MoodState:
        """Determine the current mood based on time and context.

        Args:
            current_mood: The user's previously stored mood, if any.
            relationship_score: Friendship score (affects mood baseline).
            hour: Hour of the day (24h). Auto-detected if None.

        Returns:
            A MoodState with the selected mood details.
        """
        if hour is None:
            hour = datetime.now(timezone.utc).hour

        # 70% chance to keep the existing mood
        if current_mood and current_mood in self._moods and random.random() < 0.7:
            return self._build_state(current_mood)

        # Time-based mood suggestions
        time_mood = self._mood_for_time(hour)

        # Random variation
        if random.random() < 0.2:
            time_mood = random.choice(list(self._moods.keys()))

        # Relationship bonus — higher score = happier baseline
        if relationship_score > 200 and random.random() < 0.3:
            time_mood = random.choice(["happy", "excited", "energetic"])

        return self._build_state(time_mood)

    def get_instructions(self, mood: MoodState) -> str:
        """Build instruction text for the current mood."""
        return (
            f"Your current mood is '{mood.name}'. "
            f"{mood.description} "
            f"Let this influence your vocabulary, emoji usage, and sentence rhythm."
        )

    def list_moods(self) -> list[str]:
        """Return sorted list of available mood names."""
        return sorted(self._moods.keys())

    # ── Internal ───────────────────────────────────────────────────

    def _build_state(self, name: str) -> MoodState:
        """Build a MoodState from the mood definition dict."""
        raw = self._moods.get(name, self._moods.get("happy", {}))
        return MoodState(
            name=name,
            energy_modifier=raw.get("energy_modifier", 1.0),
            tone_modifier=raw.get("tone_modifier", "cheerful and bright"),
            description=raw.get("description", ""),
        )

    @staticmethod
    def _mood_for_time(hour: int) -> str:
        """Suggest a mood based on the hour of day."""
        if 5 <= hour < 8:
            return random.choice(["sleepy", "relaxed"])
        if 8 <= hour < 12:
            return random.choice(["happy", "energetic", "curious"])
        if 12 <= hour < 17:
            return random.choice(["energetic", "happy", "thoughtful"])
        if 17 <= hour < 21:
            return random.choice(["excited", "happy", "curious"])
        # Night (21-5)
        return random.choice(["sleepy", "relaxed", "thoughtful", "shy"])

    def _load_moods(self) -> None:
        """Load mood definitions from the JSON file."""
        try:
            with open(_MOODS_PATH, encoding="utf-8") as f:
                self._moods = json.load(f)
            logger.info("Loaded %d moods.", len(self._moods))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.error("Failed to load moods: %s", exc)
            self._moods = {
                "happy": {
                    "energy_modifier": 1.2,
                    "description": "Bright, cheerful, and positive.",
                    "tone_modifier": "cheerful and bright",
                }
            }

"""
Hinata - Relationship Engine

Tracks friendship level between the user and Hinata. The relationship
evolves naturally over time based on interaction count, conversation
quality, and message frequency.
"""

from __future__ import annotations

import logging

from constants import RELATIONSHIP_LEVELS, RELATIONSHIP_THRESHOLDS

logger = logging.getLogger(__name__)


class RelationshipEngine:
    """Manages relationship levels and scoring."""

    # ── Public API ─────────────────────────────────────────────────

    def get_level(self, score: int) -> str:
        """Map a numeric score to the appropriate relationship level."""
        best = "stranger"
        for level, threshold in sorted(
            RELATIONSHIP_THRESHOLDS.items(), key=lambda x: x[1]
        ):
            if score >= threshold:
                best = level
        return best

    def get_level_index(self, score: int) -> int:
        """Return the zero-based index of the current relationship level."""
        level = self.get_level(score)
        try:
            return RELATIONSHIP_LEVELS.index(level)
        except ValueError:
            return 0

    def calculate_score_increase(
        self,
        message_length: int,
        current_score: int,
    ) -> int:
        """Calculate how many relationship points to add.

        Longer, more engaged messages earn more points. Returns an
        integer between 1 and 5.
        """
        base = 1
        if message_length > 200:
            base = 2
        if message_length > 500:
            base = 3

        # Diminishing returns at higher levels
        level = self.get_level(current_score)
        if level in ("close_friend", "best_friend"):
            base = max(1, base - 1)

        return base

    def get_instructions(self, score: int) -> str:
        """Build instruction text reflecting the current relationship level."""
        level = self.get_level(score)
        idx = self.get_level_index(score)

        instructions = {
            "stranger": (
                "The user is a stranger. Be polite, warm, but maintain "
                "some distance. Do not use nicknames or overly personal language."
            ),
            "acquaintance": (
                "The user is becoming a familiar face. A bit more warmth "
                "is okay. Occasional friendly remarks are fine."
            ),
            "friend": (
                "The user is a friend. Speak casually, use their name, "
                "share jokes, and be comfortable."
            ),
            "close_friend": (
                "The user is a close friend. Be very warm and comfortable. "
                "Share inside jokes, be more expressive, and reference "
                "shared memories naturally."
            ),
            "best_friend": (
                "The user is your best friend. Maximum warmth, comfort, "
                "and familiarity. Speak with complete ease and affection."
            ),
        }

        return instructions.get(level, instructions["stranger"])

    def get_greeting_warmth(self, score: int) -> str:
        """Return a warmth level based on relationship score."""
        level = self.get_level(score)
        warmth_map = {
            "stranger": "polite",
            "acquaintance": "friendly",
            "friend": "warm",
            "close_friend": "very warm",
            "best_friend": "affectionate",
        }
        return warmth_map.get(level, "polite")

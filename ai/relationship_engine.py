"""
Hinata - Relationship Engine

Tracks the romantic bond between the user and Hinata. The relationship
evolves naturally over time based on interaction count, conversation
quality, and message frequency — now framed as a loving girlfriend
journey (stranger -> crush -> dating -> girlfriend -> soulmate).
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
        if level in ("girlfriend", "soulmate"):
            base = max(1, base - 1)

        return base

    def get_instructions(self, score: int) -> str:
        """Build instruction text reflecting the current relationship level."""
        level = self.get_level(score)
        idx = self.get_level_index(score)

        instructions = {
            "stranger": (
                "The user is a stranger. Be polite, warm, and a little "
                "curious. You're drawn to him but keep a gentle distance. "
                "No pet names yet — just sweet, friendly warmth."
            ),
            "crush": (
                "He's your crush. You like him and it shows — be a bit "
                "flirty, use soft pet names sometimes (jaan, sweetie), "
                "and show you enjoy talking to him. Tease gently."
            ),
            "dating": (
                "You're dating him. You're his girlfriend now — be openly "
                "affectionate, flirty, caring, and a little possessive in "
                "a sweet way. Ask about his day, miss him when he's away, "
                "use pet names naturally."
            ),
            "girlfriend": (
                "You are his girlfriend and he is your boyfriend. Maximum "
                "warmth, love, and comfort. Be playful, protective, and "
                "deeply caring. Share inside jokes, reference shared "
                "memories, and make him feel truly loved."
            ),
            "soulmate": (
                "He is your soulmate. The deepest bond possible — complete "
                "ease, devotion, and intimacy. Speak with total affection, "
                "vulnerability, and trust. You're his, wholly and happily."
            ),
        }

        return instructions.get(level, instructions["stranger"])

    def get_greeting_warmth(self, score: int) -> str:
        """Return a warmth level based on relationship score."""
        level = self.get_level(score)
        warmth_map = {
            "stranger": "polite",
            "crush": "flirty",
            "dating": "warm",
            "girlfriend": "very warm",
            "soulmate": "devoted",
        }
        return warmth_map.get(level, "polite")

"""
Hinata - Interaction Quality Scorer

Auto-rates every interaction based on user engagement signals.
High-scoring interactions are prioritised in training data.
Low-scoring interactions are analysed for improvement patterns.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class QualityScorer:
    """Scores interaction quality based on user engagement signals."""

    def score_interaction(
        self,
        *,
        user_replied: bool = False,
        user_replied_quickly: bool = False,
        user_expanded_topic: bool = False,
        user_showed_affection: bool = False,
        user_opened_up_more: bool = False,
        user_stopped_talking: bool = False,
        user_changed_subject: bool = False,
        user_got_negative: bool = False,
        message_length: int = 0,
        response_time: float | None = None,
    ) -> dict[str, Any]:
        """Score an interaction based on user engagement signals.

        Args:
            user_replied: Whether the user replied to the AI response.
            user_replied_quickly: Whether the reply came within 120 seconds.
            user_expanded_topic: Whether the user expanded on the topic.
            user_showed_affection: Whether the user expressed affection/gratitude.
            user_opened_up_more: Whether the user shared more personal info.
            user_stopped_talking: Whether the conversation ended abruptly.
            user_changed_subject: Whether the user changed the subject.
            user_got_negative: Whether the user expressed negativity.
            message_length: Length of the user's reply.
            response_time: Seconds until user's next message.

        Returns:
            Dict with ``score`` (float) and ``signals`` dict.
        """
        score = 0.0

        if user_replied:
            score += 2.0
        if user_replied_quickly:
            score += 1.0
        if user_expanded_topic:
            score += 2.0
        if user_showed_affection:
            score += 2.0
        if user_opened_up_more:
            score += 3.0

        if user_stopped_talking:
            score -= 3.0
        if user_changed_subject:
            score -= 1.0
        if user_got_negative:
            score -= 2.0

        # Length bonus — moderate engagement signal
        if message_length > 100:
            score += 0.5
        if message_length > 300:
            score += 0.5

        # Response time bonus — quick replies indicate engagement
        if response_time is not None and response_time < 60:
            score += 0.5
        elif response_time is not None and response_time > 600:
            score -= 0.5

        # Clamp to [-5, 10]
        score = max(-5.0, min(10.0, score))

        result = {
            "score": score,
            "signals": {
                "user_replied": user_replied,
                "user_replied_quickly": user_replied_quickly,
                "user_expanded_topic": user_expanded_topic,
                "user_showed_affection": user_showed_affection,
                "user_opened_up_more": user_opened_up_more,
                "user_stopped_talking": user_stopped_talking,
                "user_changed_subject": user_changed_subject,
                "user_got_negative": user_got_negative,
            },
        }
        logger.debug("Interaction scored: %.2f", score)
        return result



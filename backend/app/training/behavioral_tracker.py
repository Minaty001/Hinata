"""
Hinata - Behavioral Signal Tracker

Tracks user behavioral signals over time:
- Response time patterns
- Message length trends
- Vulnerability / openness scoring
- Topic change frequency
- Emoji usage trends

These signals feed into the feeling detector and user psychology models.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Rolling window sizes
_DEFAULT_WINDOW = 10


class BehavioralTracker:
    """Tracks and computes behavioral signals from user interactions."""

    def __init__(self, window: int = _DEFAULT_WINDOW) -> None:
        self.window = window

    def compute_signals(
        self,
        *,
        current_time: float,
        last_response_time: float | None,
        message_length: int,
        message_lengths_recent: list[int],
        response_times_recent: list[float],
        emoji_count_recent: list[int],
        topic_switches_recent: list[bool],
        self_disclosures_recent: list[bool],
    ) -> dict[str, Any]:
        """Compute a full set of behavioral signals from recent interaction data.

        Args:
            current_time: Current timestamp in seconds (epoch).
            last_response_time: Seconds since last user message, or None.
            message_length: Length of the current message.
            message_lengths_recent: List of recent message lengths.
            response_times_recent: List of recent response times (seconds).
            emoji_count_recent: List of recent emoji counts per message.
            topic_switches_recent: List of bools indicating topic switches.
            self_disclosures_recent: List of bools indicating self-disclosure.

        Returns:
            Dictionary of computed behavioral signals.
        """
        signals: dict[str, Any] = {}

        # Response time
        if last_response_time is not None:
            signals["response_time_seconds"] = last_response_time
        signals["response_time_trend"] = self._compute_trend(response_times_recent)

        # Message length
        signals["message_length"] = message_length
        signals["message_length_trend"] = self._compute_trend(message_lengths_recent)

        # Vulnerability score (based on self-disclosure rate)
        if self_disclosures_recent:
            signals["self_disclosure_rate"] = float(np.mean(self_disclosures_recent))
        else:
            signals["self_disclosure_rate"] = 0.0

        # Vulnerability trend
        if len(self_disclosures_recent) >= 4:
            half = len(self_disclosures_recent) // 2
            early = float(np.mean(self_disclosures_recent[:half]))
            late = float(np.mean(self_disclosures_recent[half:]))
            if late > early + 0.1:
                signals["vulnerability_trend"] = "rising"
            elif late < early - 0.1:
                signals["vulnerability_trend"] = "dropping"
            else:
                signals["vulnerability_trend"] = "stable"
        else:
            signals["vulnerability_trend"] = "stable"

        # Topic change frequency
        if topic_switches_recent:
            signals["topic_change_frequency"] = float(np.mean(topic_switches_recent))
        else:
            signals["topic_change_frequency"] = 0.0

        # Emoji usage trend
        if len(emoji_count_recent) >= 4:
            half = len(emoji_count_recent) // 2
            early_emoji = float(np.mean(emoji_count_recent[:half]))
            late_emoji = float(np.mean(emoji_count_recent[half:]))
            if late_emoji < early_emoji - 0.3:
                signals["emoji_usage_trend"] = "dropping"
            elif late_emoji > early_emoji + 0.3:
                signals["emoji_usage_trend"] = "rising"
            else:
                signals["emoji_usage_trend"] = "stable"
        else:
            signals["emoji_usage_trend"] = "stable"

        signals["hour_of_day"] = datetime.now(timezone.utc).hour

        logger.debug("Behavioral signals computed: %s", signals)
        return signals

    # ── Internal helpers ─────────────────────────────────────────────

    @staticmethod
    def _compute_trend(values: list[float]) -> str:
        """Determine trend direction from a list of numeric values."""
        if len(values) < 4:
            return "stable"
        half = len(values) // 2
        early = float(np.mean(values[:half]))
        late = float(np.mean(values[half:]))
        threshold = 0.1 * (abs(early) + 0.01)
        if late > early + threshold:
            return "rising"
        if late < early - threshold:
            return "dropping"
        return "stable"

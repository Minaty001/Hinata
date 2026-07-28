"""
Hinata - Rate Limiter

Simple in-memory rate limiter using a sliding window approach.
Prevents individual users from sending messages too frequently.
"""

from __future__ import annotations

import time
from collections import defaultdict

from constants import RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW


class RateLimiter:
    """Per-user sliding window rate limiter.

    Tracks message timestamps per Telegram user ID and checks
    whether the user has exceeded the allowed message count
    within the time window.
    """

    def __init__(self, max_messages: int = RATE_LIMIT_MESSAGES, window: int = RATE_LIMIT_WINDOW) -> None:
        self._max_messages: int = max_messages
        self._window: int = window
        self._buckets: dict[int, list[float]] = defaultdict(list)

    def is_limited(self, user_id: int) -> bool:
        """Check if a user has exceeded the rate limit.

        Args:
            user_id: Telegram user ID.

        Returns:
            True if the user should be rate-limited.
        """
        now = time.time()
        cutoff = now - self._window

        # Prune expired timestamps
        self._buckets[user_id] = [
            ts for ts in self._buckets[user_id] if ts > cutoff
        ]

        # Check limit
        if len(self._buckets[user_id]) >= self._max_messages:
            return True

        # Record this hit
        self._buckets[user_id].append(now)
        return False


# Global rate limiter instance (cached in bot_data)
rate_limiter = RateLimiter()

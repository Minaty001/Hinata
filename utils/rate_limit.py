"""
Hinata - Rate Limiter

Simple in-memory rate limiter using a sliding window approach.
Prevents individual users from sending messages too frequently.
"""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from functools import wraps
from typing import Any

from telegram import Update
from telegram.ext import ContextTypes

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

    def remaining(self, user_id: int) -> int:
        """Return how many messages the user can still send in the current window."""
        now = time.time()
        cutoff = now - self._window
        self._buckets[user_id] = [
            ts for ts in self._buckets[user_id] if ts > cutoff
        ]
        return max(0, self._max_messages - len(self._buckets[user_id]))

    def reset(self, user_id: int) -> None:
        """Clear the rate limit bucket for a user."""
        self._buckets.pop(user_id, None)


# Global rate limiter instance (cached in bot_data)
rate_limiter = RateLimiter()


def rate_limit_decorator(
    max_messages: int = RATE_LIMIT_MESSAGES,
    window: int = RATE_LIMIT_WINDOW,
) -> Callable:
    """Decorator that applies rate limiting to a handler function.

    Usage::

        @rate_limit_decorator()
        async def my_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            ...

    If rate-limited, sends a friendly warning and does not call the handler.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Any:
            if update.effective_user:
                limiter = context.bot_data.get("rate_limiter", rate_limiter)
                if limiter.is_limited(update.effective_user.id):
                    await update.message.reply_text(
                        "Whoa, slow down! 😅 Give me a moment to breathe. "
                        "Try again in a few seconds.",
                    )
                    return None
            return await func(update, context)
        return wrapper
    return decorator

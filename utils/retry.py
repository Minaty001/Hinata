"""
Hinata - Retry Utility

Generic async retry decorator for functions that may fail transiently.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator that retries an async function on failure.

    Args:
        max_attempts: Maximum number of attempts (including the first).
        delay: Initial delay in seconds between retries.
        backoff: Multiplier for delay after each retry.
        exceptions: Tuple of exception types that trigger a retry.

    Usage::

        @async_retry(max_attempts=3, delay=1.0)
        async def fetch_data() -> dict:
            ...
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt < max_attempts:
                        logger.warning(
                            "%s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                            func.__name__,
                            attempt,
                            max_attempts,
                            exc,
                            current_delay,
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__,
                            max_attempts,
                            exc,
                        )

            raise last_exc  # type: ignore[misc]
        return wrapper  # type: ignore[return-value]
    return decorator

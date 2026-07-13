"""
Hinata - Helper Utilities

General-purpose helper functions used across the application.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def format_timestamp(dt: datetime | None, fmt: str = "%Y-%m-%d %H:%M UTC") -> str:
    """Format a datetime object as a readable string.

    Args:
        dt: The datetime to format. Uses current time if None.
        fmt: strftime format string.

    Returns:
        Formatted timestamp string.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime(fmt)


def pluralise(count: int, singular: str, plural: str | None = None) -> str:
    """Return a singular or plural noun phrase based on count.

    Args:
        count: The number of items.
        singular: The singular form (e.g. "message").
        plural: The plural form (defaults to singular + "s").

    Returns:
        ``"1 message"`` or ``"5 messages"``.
    """
    if plural is None:
        plural = f"{singular}s"
    return f"{count} {singular if count == 1 else plural}"


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with an ellipsis if it exceeds max_length.

    Args:
        text: The text to truncate.
        max_length: Maximum character length.

    Returns:
        Truncated text with ``…`` appended if cut.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 1].rsplit(" ", 1)[0] + " …"


def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely traverse a nested dict without raising KeyError.

    Args:
        data: The nested dictionary.
        keys: Sequence of keys to traverse.
        default: Fallback value if any key is missing.

    Returns:
        The value at the nested path, or ``default``.
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, {})
        else:
            return default
    return current if current != {} else default

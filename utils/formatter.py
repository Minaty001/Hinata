"""
Hinata - Formatter Utilities

Text formatting helpers for Telegram message presentation.
"""

from __future__ import annotations

from datetime import datetime, timezone


def bold(text: str) -> str:
    """Format text as Telegram Markdown bold."""
    return f"*{text}*"


def code(text: str) -> str:
    """Format text as inline code."""
    return f"`{text}`"


def code_block(text: str, language: str = "") -> str:
    """Format text as a code block."""
    return f"```{language}\n{text}\n```"


def bullet_list(items: list[str]) -> str:
    """Format a list of strings as a Markdown bullet list."""
    return "\n".join(f"• {item}" for item in items)


def key_value(key: str, value: str, separator: str = ": ") -> str:
    """Format a key-value pair."""
    return f"*{key}*{separator}{value}"


def timestamp(format: str = "%Y-%m-%d %H:%M:%S UTC") -> str:
    """Return current UTC timestamp as a formatted string."""
    return datetime.now(timezone.utc).strftime(format)

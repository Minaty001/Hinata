"""
Hinata - Input Validators

Utilities for validating and sanitising user input before processing.
"""

from __future__ import annotations

import re


def sanitise_input(text: str) -> str:
    """Strip potentially harmful content from user input.

    - Removes null bytes.
    - Strips leading/trailing whitespace.
    - Limits consecutive newlines.

    Args:
        text: Raw user input.

    Returns:
        Sanitised text.
    """
    # Remove null bytes
    text = text.replace("\x00", "")

    # Strip whitespace
    text = text.strip()

    # Collapse excessive newlines
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    return text


def is_owner(telegram_id: int, owner_id: int) -> bool:
    """Check if a Telegram user is the bot owner."""
    return telegram_id == owner_id

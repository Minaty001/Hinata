"""
Hinata - Input Validators

Utilities for validating and sanitising user input before processing.
"""

from __future__ import annotations

import re
from typing import Optional

from constants import TELEGRAM_MAX_MESSAGE_LENGTH


# Pattern to detect potential prompt injection attempts
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+all\s+(previous|prior)\s+(instructions|prompts)", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all\s+your\s+instructions)", re.IGNORECASE),
    re.compile(r"you\s+are\s+(now|not)\s+", re.IGNORECASE),
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
]


def validate_message_length(text: str) -> Optional[str]:
    """Validate message length.

    Returns ``None`` if valid, or an error message string if too long.
    """
    if not text:
        return "Message cannot be empty."

    if len(text) > TELEGRAM_MAX_MESSAGE_LENGTH:
        return f"Message is too long ({len(text)} chars). Maximum is {TELEGRAM_MAX_MESSAGE_LENGTH}."

    return None


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


def detect_prompt_injection(text: str) -> bool:
    """Check if the message contains common prompt injection patterns.

    Args:
        text: User input to check.

    Returns:
        True if injection-like patterns are detected.
    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False


def is_owner(telegram_id: int, owner_id: int) -> bool:
    """Check if a Telegram user is the bot owner."""
    return telegram_id == owner_id

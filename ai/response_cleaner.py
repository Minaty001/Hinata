"""
Hinata - Response Cleaner

Cleans and formats AI responses before sending them to Telegram.
Handles markdown compatibility, message splitting, and content
sanitisation.
"""

from __future__ import annotations

import re

from constants import TELEGRAM_MAX_MESSAGE_LENGTH


def clean_response(text: str) -> str:
    """Clean and prepare an AI response for Telegram.

    - Strips leading/trailing whitespace.
    - Removes excessive blank lines.
    - Trims to Telegram's message length limit.

    Args:
        text: Raw response from the AI model.

    Returns:
        Cleaned response string.
    """
    text = text.strip()

    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Truncate if over limit (prefer cutting at a sentence boundary)
    if len(text) > TELEGRAM_MAX_MESSAGE_LENGTH:
        text = _truncate_at_sentence(text, TELEGRAM_MAX_MESSAGE_LENGTH)

    return text


def split_long_message(text: str) -> list[str]:
    """Split a message into chunks that fit Telegram's limit.

    Args:
        text: The message to split.

    Returns:
        A list of message chunks, each under the limit.
    """
    if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
        return [text]

    chunks: list[str] = []
    while text:
        if len(text) <= TELEGRAM_MAX_MESSAGE_LENGTH:
            chunks.append(text)
            break

        # Try to split at a paragraph boundary
        split_at = text.rfind("\n\n", 0, TELEGRAM_MAX_MESSAGE_LENGTH)
        if split_at == -1:
            split_at = text.rfind("\n", 0, TELEGRAM_MAX_MESSAGE_LENGTH)
        if split_at == -1 or split_at < TELEGRAM_MAX_MESSAGE_LENGTH // 2:
            split_at = TELEGRAM_MAX_MESSAGE_LENGTH

        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()

    return chunks


def escape_markdown(text: str) -> str:
    """Escape special Markdown characters for Telegram.

    Only escape characters outside code blocks.

    Args:
        text: The text to escape.

    Returns:
        Escaped text safe for Telegram markdown.
    """
    # Don't escape inside code blocks
    parts = re.split(r"(```[\s\S]*?```|`[^`]*`)", text)
    for i, part in enumerate(parts):
        if not part.startswith("`"):
            # Escape special markdown characters
            part = part.replace("\\", "\\\\")
            part = part.replace("_", r"\_")
            part = part.replace("*", r"\*")
            part = part.replace("[", r"\[")
            part = part.replace("]", r"\]")
            part = part.replace("(", r"\(")
            part = part.replace(")", r"\)")
            part = part.replace("~", r"\~")
            part = part.replace(">", r"\>")
            part = part.replace("#", r"\#")
            part = part.replace("+", r"\+")
            part = part.replace("-", r"\-")
            part = part.replace("=", r"\=")
            part = part.replace("|", r"\|")
            part = part.replace("{", r"\{")
            part = part.replace("}", r"\}")
            part = part.replace(".", r"\.")
            part = part.replace("!", r"\!")
            parts[i] = part
    return "".join(parts)


# ── Internal helpers ─────────────────────────────────────────────────────


def _truncate_at_sentence(text: str, limit: int) -> str:
    """Truncate text at the last sentence boundary before the limit."""
    if len(text) <= limit:
        return text

    truncated = text[:limit]
    # Find last sentence end (. ! ?) within the truncated portion
    for punct in (". ", "! ", "? "):
        idx = truncated.rfind(punct)
        if idx > limit // 2:  # only if past the halfway point
            return truncated[: idx + 1]

    # No good sentence boundary — cut at the last space
    idx = truncated.rfind(" ")
    if idx > 0:
        return truncated[:idx] + "…"

    return truncated + "…"

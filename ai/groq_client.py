"""
Hinata - Groq API Client

Async HTTP client for the Groq API with retry logic, timeout handling,
and error management. All AI provider calls go through this layer so the
rest of the application never talks to Groq directly.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from config import settings
from constants import GROQ_MAX_TOKENS, GROQ_MODEL, GROQ_RETRIES, GROQ_RETRY_DELAY, GROQ_TEMPERATURE, GROQ_TIMEOUT

logger = logging.getLogger(__name__)

GROQ_API_BASE = "https://api.groq.com/openai/v1/chat/completions"


class GroqClientError(Exception):
    """Base exception for Groq API errors."""


class GroqRateLimitError(GroqClientError):
    """Raised when Groq returns a 429 rate-limit response."""


class GroqAuthError(GroqClientError):
    """Raised when the API key is invalid or missing."""


class GroqClient:
    """Async client for the Groq API.

    Wraps the chat completions endpoint with retry, timeout, and
    structured error handling.
    """

    def __init__(self) -> None:
        self._api_key: str = settings.GROQ_API_KEY
        self._headers: dict[str, str] = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str = GROQ_MODEL,
        max_tokens: int = GROQ_MAX_TOKENS,
        temperature: float = GROQ_TEMPERATURE,
    ) -> str:
        """Send a chat completion request to Groq.

        Args:
            messages: List of message dicts with ``role`` and ``content`` keys.
            model: The Groq model identifier.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0.0 – 2.0).

        Returns:
            The generated response text.

        Raises:
            GroqAuthError: If the API key is invalid.
            GroqRateLimitError: If rate limited after all retries.
            GroqClientError: For other API or network failures.
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        last_exception: Exception | None = None

        for attempt in range(1, GROQ_RETRIES + 2):
            try:
                async with httpx.AsyncClient(timeout=GROQ_TIMEOUT) as client:
                    response = await client.post(
                        GROQ_API_BASE,
                        headers=self._headers,
                        json=payload,
                    )

                if response.status_code == 200:
                    data = response.json()
                    content: str = data["choices"][0]["message"]["content"]
                    logger.debug("Groq response received (%d chars).", len(content))
                    return content

                if response.status_code == 401:
                    raise GroqAuthError("Invalid or missing Groq API key.")

                if response.status_code == 429:
                    retry_after = _parse_retry_after(response)
                    logger.warning(
                        "Groq rate limited (attempt %d/%d). Retrying in %.1fs...",
                        attempt,
                        GROQ_RETRIES + 1,
                        retry_after,
                    )
                    await asyncio.sleep(retry_after)
                    continue

                # Other server errors
                logger.warning(
                    "Groq returned %d (attempt %d/%d): %.200s",
                    response.status_code,
                    attempt,
                    GROQ_RETRIES + 1,
                    response.text,
                )

            except httpx.TimeoutException as exc:
                logger.warning(
                    "Groq timeout (attempt %d/%d).", attempt, GROQ_RETRIES + 1
                )
                last_exception = exc
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "Groq HTTP error (attempt %d/%d): %s",
                    attempt,
                    GROQ_RETRIES + 1,
                    exc,
                )
                last_exception = exc
            except httpx.RequestError as exc:
                logger.warning(
                    "Groq request failed (attempt %d/%d): %s",
                    attempt,
                    GROQ_RETRIES + 1,
                    exc,
                )
                last_exception = exc

            # Wait before retry (except on last attempt)
            if attempt <= GROQ_RETRIES:
                await asyncio.sleep(GROQ_RETRY_DELAY * attempt)

        raise GroqClientError(
            f"Groq API failed after {GROQ_RETRIES + 1} attempts."
        ) from last_exception


def _parse_retry_after(response: httpx.Response) -> float:
    """Extract the Retry-After header value, defaulting to 5 seconds."""
    raw = response.headers.get("Retry-After", "5")
    try:
        return float(raw)
    except ValueError:
        return 5.0

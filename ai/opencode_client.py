"""
Hinata - OpenCode Zen API Client

Async HTTP client for OpenCode Zen API (https://opencode.ai/zen/v1) supporting
free thinking and complex conversation models (opencode-zen-free, deepseek-r1, etc.).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from config import settings
from constants import (
    GROQ_MAX_TOKENS,
    GROQ_TEMPERATURE,
    OPENCODE_ZEN_DEFAULT_BASE_URL,
    OPENCODE_ZEN_DEFAULT_MODEL,
    OPENCODE_ZEN_RETRIES,
    OPENCODE_ZEN_RETRY_DELAY,
    OPENCODE_ZEN_TIMEOUT,
)

logger = logging.getLogger(__name__)


class OpenCodeZenClientError(Exception):
    """Base exception for OpenCode Zen API errors."""


class OpenCodeZenAuthError(OpenCodeZenClientError):
    """Raised when authentication fails."""


class OpenCodeZenRateLimitError(OpenCodeZenClientError):
    """Raised when rate limited."""


class OpenCodeZenClient:
    """Async client for the OpenCode Zen API endpoint (https://opencode.ai/zen/v1).

    Wraps chat completions with support for free thinking and reasoning models,
    retries, and structured error handling.
    """

    def __init__(self) -> None:
        raw_base = getattr(settings, "OPENCODE_ZEN_BASE_URL", OPENCODE_ZEN_DEFAULT_BASE_URL)
        self.base_url: str = raw_base.rstrip("/")
        if not self.base_url.endswith("/chat/completions"):
            self.endpoint: str = f"{self.base_url}/chat/completions"
        else:
            self.endpoint = self.base_url

        self.api_key: str = getattr(settings, "OPENCODE_ZEN_API_KEY", "")
        self.default_model: str = getattr(settings, "OPENCODE_ZEN_MODEL", OPENCODE_ZEN_DEFAULT_MODEL)

    def _build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @staticmethod
    def _normalize_model_name(model_name: str) -> str:
        """Resolve model names/aliases to exact OpenCode Zen API model IDs."""
        name = model_name.strip()
        if name.startswith("opencode/"):
            name = name[len("opencode/"):]
        elif name.startswith("pencode/"):
            name = name[len("pencode/"):]

        aliases = {
            "opencode-zen-free": "big-pickle",
            "ing-3.0-flash-free": "ling-3.0-flash-free",
        }
        return aliases.get(name, name)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = GROQ_MAX_TOKENS,
        temperature: float = GROQ_TEMPERATURE,
    ) -> str:
        """Send a chat completion request to OpenCode Zen API.

        Args:
            messages: List of message dicts with ``role`` and ``content`` keys.
            model: The OpenCode model identifier (e.g. opencode/big-pickle, opencode-zen-free).
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            The generated response text.
        """
        raw_model = model or self.default_model
        target_model = self._normalize_model_name(raw_model)
        payload: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        headers = self._build_headers()
        last_exception: Exception | None = None

        for attempt in range(1, OPENCODE_ZEN_RETRIES + 2):
            try:
                async with httpx.AsyncClient(timeout=OPENCODE_ZEN_TIMEOUT) as client:
                    response = await client.post(
                        self.endpoint,
                        headers=headers,
                        json=payload,
                    )

                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        msg = choices[0]["message"]
                        content: str = msg.get("content") or msg.get("reasoning") or ""
                        logger.debug("OpenCode Zen response received (%d chars).", len(content))
                        return content

                if response.status_code == 401:
                    raise OpenCodeZenAuthError("Unauthorized access to OpenCode Zen API.")

                if response.status_code == 429:
                    logger.warning(
                        "OpenCode Zen rate limited (attempt %d/%d). Retrying in %.1fs...",
                        attempt,
                        OPENCODE_ZEN_RETRIES + 1,
                        5.0,
                    )
                    await asyncio.sleep(5.0)
                    continue

                logger.warning(
                    "OpenCode Zen API returned %d (attempt %d/%d): %.200s",
                    response.status_code,
                    attempt,
                    OPENCODE_ZEN_RETRIES + 1,
                    response.text,
                )

            except httpx.TimeoutException as exc:
                logger.warning("OpenCode Zen API timeout (attempt %d/%d).", attempt, OPENCODE_ZEN_RETRIES + 1)
                last_exception = exc
            except httpx.RequestError as exc:
                logger.warning("OpenCode Zen API request failed (attempt %d/%d): %s", attempt, OPENCODE_ZEN_RETRIES + 1, exc)
                last_exception = exc

            if attempt <= OPENCODE_ZEN_RETRIES:
                await asyncio.sleep(OPENCODE_ZEN_RETRY_DELAY * attempt)

        raise OpenCodeZenClientError(
            f"OpenCode Zen API call failed after {OPENCODE_ZEN_RETRIES + 1} attempts."
        ) from last_exception

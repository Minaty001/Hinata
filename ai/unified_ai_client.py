"""
Hinata - Unified AI Client Manager

Provides a unified interface for AI LLM completions supporting multiple providers:
- Groq API (GroqClient)
- OpenCode Zen API (OpenCodeZenClient - https://opencode.ai/zen/v1)

Includes dynamic provider switching and seamless failover capabilities.
"""

from __future__ import annotations

import logging

from ai.groq_client import GroqClient, GroqClientError
from ai.opencode_client import OpenCodeZenClient, OpenCodeZenClientError
from config import settings
from constants import (
    GROQ_MAX_TOKENS,
    GROQ_MODEL,
    GROQ_TEMPERATURE,
    OPENCODE_ZEN_DEFAULT_MODEL,
)

logger = logging.getLogger(__name__)


class UnifiedAIClient:
    """Unified AI Client managing primary AI provider and automated fallback."""

    def __init__(self) -> None:
        self.groq_client = GroqClient()
        self.opencode_client = OpenCodeZenClient()
        self.provider: str = getattr(settings, "AI_PROVIDER", "groq").lower()
        self.fallback_enabled: bool = getattr(settings, "ENABLE_AI_FALLBACK", True)
        self.opencode_model: str = getattr(settings, "OPENCODE_ZEN_MODEL", OPENCODE_ZEN_DEFAULT_MODEL)
        self.groq_model: str = GROQ_MODEL

    def get_active_provider(self) -> str:
        """Return the current active provider name."""
        return self.provider

    def set_active_provider(self, provider: str, model: str | None = None) -> None:
        """Set the active provider and optionally set model."""
        clean_provider = provider.lower()
        if clean_provider in ("groq", "opencode", "opencode_zen", "zen"):
            if clean_provider in ("opencode", "zen"):
                clean_provider = "opencode_zen"
            self.provider = clean_provider
            if model:
                if clean_provider == "opencode_zen":
                    self.opencode_model = model
                else:
                    self.groq_model = model
            logger.info("Active AI provider changed to %s (model: %s).", self.provider, model or "default")

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = GROQ_MAX_TOKENS,
        temperature: float = GROQ_TEMPERATURE,
    ) -> str:
        """Send chat completion to the active provider with automatic fallback.

        Args:
            messages: Conversation message list.
            model: Optional override model identifier.
            max_tokens: Token limit.
            temperature: Sampling temperature.

        Returns:
            The generated assistant text response.
        """
        primary = self.provider

        # Attempt 1: Primary provider
        try:
            if primary == "opencode_zen":
                target_model = model or self.opencode_model
                logger.debug("Requesting chat completion from OpenCode Zen (%s)...", target_model)
                return await self.opencode_client.chat_completion(
                    messages,
                    model=target_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                target_model = model or self.groq_model
                logger.debug("Requesting chat completion from Groq (%s)...", target_model)
                return await self.groq_client.chat_completion(
                    messages,
                    model=target_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
        except Exception as primary_error:
            logger.warning(
                "Primary AI provider '%s' failed: %s",
                primary,
                primary_error,
            )
            if not self.fallback_enabled:
                raise primary_error

        # Attempt 2: Fallback provider
        secondary = "groq" if primary == "opencode_zen" else "opencode_zen"
        logger.info("Falling back to secondary AI provider '%s'...", secondary)

        try:
            if secondary == "opencode_zen":
                return await self.opencode_client.chat_completion(
                    messages,
                    model=self.opencode_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            else:
                return await self.groq_client.chat_completion(
                    messages,
                    model=self.groq_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
        except Exception as secondary_error:
            logger.error("Secondary AI provider '%s' also failed: %s", secondary, secondary_error)
            raise secondary_error

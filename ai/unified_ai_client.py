"""
Hinata - Unified AI Client Manager

Provides a unified interface supporting multiple AI providers:
- Groq API (groq)
- OpenCode Zen API (opencode_zen)
- OpenAI API (openai)
- Google Gemini API (gemini)
- OpenRouter API (openrouter)
- Bytez API (bytez)

Features:
- Separate per-provider configuration (API key, Base URL, active model selection).
- Automatic model matching (prevents 404 cross-provider model mismatches).
- Automated secondary provider failover.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

from config import settings
from constants import (
    GROQ_MAX_TOKENS,
    GROQ_TEMPERATURE,
    PROVIDER_CATALOG,
)

logger = logging.getLogger(__name__)


class UnifiedAIClient:
    """Unified multi-provider AI client with dynamic switching and automated fallback."""

    def __init__(self) -> None:
        self.active_provider: str = getattr(settings, "AI_PROVIDER", "groq").lower()
        self.fallback_enabled: bool = getattr(settings, "ENABLE_AI_FALLBACK", True)

        # Initialize configurations for all 6 providers
        self.providers: dict[str, dict[str, Any]] = {}
        for prov_key, catalog in PROVIDER_CATALOG.items():
            env_key = f"{prov_key.upper()}_API_KEY"
            api_key = getattr(settings, env_key, os.getenv(env_key, ""))
            if prov_key == "groq" and not api_key:
                api_key = getattr(settings, "GROQ_API_KEY", "")
            elif prov_key == "opencode_zen" and not api_key:
                api_key = getattr(settings, "OPENCODE_ZEN_API_KEY", "")

            base_url = getattr(settings, f"{prov_key.upper()}_BASE_URL", catalog["default_base_url"])

            self.providers[prov_key] = {
                "name": catalog["name"],
                "api_key": api_key,
                "base_url": base_url.rstrip("/"),
                "active_model": catalog["default_model"],
                "models": list(catalog["models"]),
            }

    def get_active_provider(self) -> str:
        """Return active provider key."""
        return self.active_provider

    def set_active_provider(self, provider: str, model: str | None = None) -> None:
        """Switch active provider and set/validate model."""
        clean = provider.lower()
        if clean in ("opencode", "zen"):
            clean = "opencode_zen"

        if clean in self.providers:
            self.active_provider = clean

            # Model validation: ensure model belongs to selected provider
            if model:
                supported_models = self.providers[clean]["models"]
                if model in supported_models or "/" in model or "-" in model:
                    # If model passed belongs to another known provider, default to this provider's active model
                    other_provider_match = False
                    for other_k, other_v in self.providers.items():
                        if other_k != clean and model in other_v["models"]:
                            other_provider_match = True
                            break

                    if not other_provider_match:
                        self.providers[clean]["active_model"] = model
                        if model not in supported_models:
                            self.providers[clean]["models"].append(model)
                    else:
                        logger.info("Model '%s' belongs to another provider. Using %s's active model '%s'.", model, clean, self.providers[clean]["active_model"])
                else:
                    self.providers[clean]["active_model"] = model

            logger.info("Active AI provider set to %s (model: %s).", self.active_provider, self.providers[clean]["active_model"])

    def set_provider_config(
        self,
        provider: str,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        """Update provider API settings."""
        clean = provider.lower()
        if clean in ("opencode", "zen"):
            clean = "opencode_zen"

        if clean not in self.providers:
            self.providers[clean] = {
                "name": clean.capitalize(),
                "api_key": api_key or "",
                "base_url": base_url or "",
                "active_model": model or "default",
                "models": [model] if model else [],
            }
            return

        if api_key is not None:
            self.providers[clean]["api_key"] = api_key.strip()
        if base_url is not None:
            self.providers[clean]["base_url"] = base_url.strip().rstrip("/")
        if model is not None and model.strip():
            m_clean = model.strip()
            self.providers[clean]["active_model"] = m_clean
            if m_clean not in self.providers[clean]["models"]:
                self.providers[clean]["models"].append(m_clean)

        logger.info("Updated provider config for %s: model=%s, base_url=%s", clean, self.providers[clean]["active_model"], self.providers[clean]["base_url"])

    def get_all_providers_info(self) -> dict[str, Any]:
        """Return catalog and configuration for all providers."""
        out = {}
        for k, v in self.providers.items():
            out[k] = {
                "name": v["name"],
                "api_key": v["api_key"],
                "base_url": v["base_url"],
                "active_model": v["active_model"],
                "models": v["models"],
                "is_active": (k == self.active_provider),
            }
        return out

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = GROQ_MAX_TOKENS,
        temperature: float = GROQ_TEMPERATURE,
    ) -> str:
        """Execute chat completion against active provider with fallback."""
        primary = self.active_provider
        try:
            return await self._call_provider(primary, messages, model=model, max_tokens=max_tokens, temperature=temperature)
        except Exception as primary_error:
            logger.warning("Primary AI provider '%s' failed: %s", primary, primary_error)
            if not self.fallback_enabled:
                raise primary_error

        # Fallback loop across other available providers with valid API keys or free endpoints
        for fallback_prov in self.providers.keys():
            if fallback_prov == primary:
                continue
            logger.info("Attempting fallback provider '%s'...", fallback_prov)
            try:
                return await self._call_provider(fallback_prov, messages, max_tokens=max_tokens, temperature=temperature)
            except Exception as fb_err:
                logger.warning("Fallback provider '%s' also failed: %s", fallback_prov, fb_err)

        raise RuntimeError("All AI providers failed to generate completion.")

    async def _call_provider(
        self,
        provider_key: str,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        max_tokens: int = GROQ_MAX_TOKENS,
        temperature: float = GROQ_TEMPERATURE,
    ) -> str:
        """Call specific provider REST API."""
        cfg = self.providers.get(provider_key)
        if not cfg:
            raise ValueError(f"Unknown provider: {provider_key}")

        target_model = model or cfg["active_model"]

        # Validate target_model against provider
        if model and model not in cfg["models"]:
            # Check if requested model belongs to another provider
            for other_k, other_v in self.providers.items():
                if other_k != provider_key and model in other_v["models"]:
                    target_model = cfg["active_model"]
                    break

        base_url = cfg["base_url"]
        if not base_url.endswith("/chat/completions"):
            endpoint = f"{base_url}/chat/completions"
        else:
            endpoint = base_url

        headers = {"Content-Type": "application/json"}
        api_key = cfg["api_key"]
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
            if provider_key == "gemini":
                headers["x-goog-api-key"] = api_key

        payload = {
            "model": target_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        logger.debug("Calling %s (%s) at %s...", provider_key, target_model, endpoint)

        async with httpx.AsyncClient(timeout=35.0) as client:
            response = await client.post(endpoint, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                choice = data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
                if "text" in choice:
                    return choice["text"]
            raise ValueError(f"Unexpected response format from {provider_key}: {response.text[:200]}")

        raise RuntimeError(f"Provider {provider_key} returned HTTP {response.status_code}: {response.text[:250]}")

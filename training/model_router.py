"""
Hinata - Model Router

Selects provider and temperature per response mode.
Simple dict lookup — no capability-scoring matrix needed.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Per-mode provider preference + temperature
# Emotional modes → OpenCode Zen (better nuance)
# Analytical/fast modes → Groq (faster, more precise)
_MODE_CONFIG: dict[str, dict[str, Any]] = {
    "comfort": {"provider": "opencode_zen", "temperature": 0.85},
    "space": {"provider": "groq", "temperature": 0.6},
    "grounding": {"provider": "opencode_zen", "temperature": 0.65},
    "celebration": {"provider": "opencode_zen", "temperature": 0.9},
    "supportive_challenge": {"provider": "groq", "temperature": 0.7},
    "playful": {"provider": "opencode_zen", "temperature": 0.95},
    "intimate": {"provider": "opencode_zen", "temperature": 0.8},
    "gentle_presence": {"provider": "groq", "temperature": 0.6},
}


class ModelRouter:
    """Stateless router — select() delegates to select_route()."""

    @staticmethod
    def select(**kwargs: Any) -> dict[str, Any]:
        return select_route(**kwargs)


def select_route(
    *,
    response_mode: str,
    available_providers: list[str] | None = None,
    active_provider: str = "groq",
) -> dict[str, Any]:
    """Select provider and temperature for the given response mode.

    Falls back to the active provider when the preferred one is unavailable.
    """
    config = _MODE_CONFIG.get(response_mode, _MODE_CONFIG["comfort"])
    preferred = config["provider"]
    temperature = config["temperature"]

    if available_providers and preferred not in available_providers:
        preferred = active_provider

    return {
        "provider": preferred,
        "temperature": temperature,
        "reason": f"mode={response_mode} → {preferred} @ t={temperature}",
    }

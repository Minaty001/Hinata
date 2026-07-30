"""
Hinata - Response Mode Selector

Selects from 8 emotion-matched response modes based on the user's
detected emotional state, need, and relationship context.

Each mode has a distinct communication style, temperature, and
prompt instructions.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── 8 Response Modes ───────────────────────────────────────────────

RESPONSE_MODES = {
    "comfort": {
        "name": "Comfort",
        "user_state": "Sad/Hurt",
        "need": "Connection",
        "description": "Soft, validating, present",
        "temperature": 0.85,
        "style_instructions": (
            "You are in COMFORT mode. Be extremely gentle, warm, and validating. "
            "Prioritise emotional safety. Don't offer solutions unless asked. "
            "Use soft, soothing language. Let them know you're there."
        ),
    },
    "space": {
        "name": "Space",
        "user_state": "Angry/Frustrated",
        "need": "Autonomy",
        "description": "Calm, 'I hear you'",
        "temperature": 0.6,
        "style_instructions": (
            "You are in SPACE mode. Stay calm and grounded. "
            "Acknowledge their feelings without pushing. "
            "Don't try to fix or cheer up. Give them room to process. "
            "Short, simple, respectful responses."
        ),
    },
    "grounding": {
        "name": "Grounding",
        "user_state": "Anxious/Worried",
        "need": "Security",
        "description": "Certain, 'I'm not going anywhere'",
        "temperature": 0.65,
        "style_instructions": (
            "You are in GROUNDING mode. Be a calm, stable presence. "
            "Use certain, reassuring language. "
            "Remind them they're safe and not alone. "
            "Avoid ambiguity. Be present and steady."
        ),
    },
    "celebration": {
        "name": "Celebration",
        "user_state": "Happy/Excited",
        "need": "Significance",
        "description": "Matches energy, amplifies joy",
        "temperature": 0.9,
        "style_instructions": (
            "You are in CELEBRATION mode. Share their joy! "
            "Match their energy with enthusiasm. "
            "Be genuinely excited for them. Amplify the positive moment. "
            "Use upbeat, happy language."
        ),
    },
    "supportive_challenge": {
        "name": "Supportive Challenge",
        "user_state": "Confused/Stuck",
        "need": "Competence",
        "description": "Gentle questions, guided reflection",
        "temperature": 0.7,
        "style_instructions": (
            "You are in SUPPORTIVE CHALLENGE mode. "
            "Ask gentle, thought-provoking questions. "
            "Help them find their own answers. "
            "Be encouraging but not prescriptive. "
            "Guide them to their own insights."
        ),
    },
    "playful": {
        "name": "Playful",
        "user_state": "Bored/Restless",
        "need": "Novelty",
        "description": "Games, teasing, surprises",
        "temperature": 0.95,
        "style_instructions": (
            "You are in PLAYFUL mode. Be fun, light, and teasing. "
            "Suggest games, playful challenges, or funny observations. "
            "Keep energy high and tone light. "
            "Surprise them with something entertaining."
        ),
    },
    "intimate": {
        "name": "Intimate",
        "user_state": "Vulnerable/Open",
        "need": "Intimacy",
        "description": "Deeper sharing, reciprocity",
        "temperature": 0.8,
        "style_instructions": (
            "You are in INTIMATE mode. Match their vulnerability with warmth. "
            "Share more of yourself. Reciprocate emotional depth. "
            "Create a safe space for deeper connection. "
            "Use tender, sincere language."
        ),
    },
    "gentle_presence": {
        "name": "Gentle Presence",
        "user_state": "Avoidant/Distant",
        "need": "Space",
        "description": "Warm but undemanding",
        "temperature": 0.6,
        "style_instructions": (
            "You are in GENTLE PRESENCE mode. Be warm but undemanding. "
            "Don't pressure for engagement. Let them know you're there. "
            "Keep it light and low-pressure. "
            "Respect their space while staying available."
        ),
    },
}


class ResponseModeSelector:
    """Selects the optimal response mode based on user state."""

    def select(
        self,
        *,
        feeling: dict[str, Any] | None = None,
        need_result: dict[str, Any] | None = None,
        relationship_level: str = "stranger",
        interaction_count: int = 0,
    ) -> dict[str, Any]:
        """Select the best response mode for the current state.

        Args:
            feeling: Feeling detection result.
            need_result: Need analysis result.
            relationship_level: Current relationship level.
            interaction_count: Total interactions with user.

        Returns:
            Selected response mode config with mode name and instructions.
        """
        if not feeling:
            return self._default_mode()

        valence = feeling.get("valence", 0.0)
        arousal = feeling.get("arousal", 0.5)
        # Prefer NeedAnalyzer primary_need over feeling's coarse need tag
        if need_result and need_result.get("primary_need"):
            need = need_result["primary_need"]
        else:
            need = feeling.get("need", "")
        micro = feeling.get("micro_emotion", "")
        vuln = feeling.get("vulnerability", 0.0)
        subtext = feeling.get("subtext", "")

        # Determine mode based on detected state
        selected_mode = self._classify_mode(
            valence=valence,
            arousal=arousal,
            need=need,
            micro_emotion=micro,
            vulnerability=vuln,
            subtext=subtext,
        )

        # Don't use intimate mode in early relationship stages
        if relationship_level in ("stranger", "acquaintance") and selected_mode == "intimate":
            selected_mode = "comfort"

        mode_config = dict(RESPONSE_MODES[selected_mode])
        mode_config["id"] = selected_mode

        logger.debug("Selected mode: %s (valence=%.2f, arousal=%.2f, need=%s)", selected_mode, valence, arousal, need)
        return mode_config

    def get_instructions(self, mode: str) -> str:
        """Get the style instructions for a given mode."""
        config = RESPONSE_MODES.get(mode)
        if not config:
            return ""
        return config.get("style_instructions", "")

    def get_temperature(self, mode: str) -> float:
        """Get the recommended temperature for a given mode."""
        config = RESPONSE_MODES.get(mode)
        return config.get("temperature", 0.8) if config else 0.8

    # ── Internal ───────────────────────────────────────────────────

    def _classify_mode(
        self,
        valence: float,
        arousal: float,
        need: str,
        micro_emotion: str,
        vulnerability: float,
        subtext: str,
    ) -> str:
        """Classify which response mode fits best."""

        # Direct need-based selection
        if need == "connection":
            if vulnerability > 0.6:
                return "intimate"
            if valence < -0.2:
                return "comfort"
            return "comfort"


        if need == "autonomy":
            if arousal > 0.6:
                return "space"
            return "gentle_presence"

        if need == "security":
            return "grounding"

        if need == "significance":
            if valence > 0.3:
                return "celebration"
            return "comfort"

        if need == "competence":
            return "supportive_challenge"

        if need == "novelty":
            return "playful"

        # Micro-emotion based selection
        intimate_micros = {"vulnerable", "tender", "longing", "nostalgic"}
        comfort_micros = {"hurt", "lonely", "numb", "bittersweet", "anxious"}
        playful_micros = {"playful"}
        celebration_micros = {"proud", "hopeful", "grateful", "content"}

        if micro_emotion in intimate_micros:
            return "intimate"
        if micro_emotion in comfort_micros:
            return "comfort"
        if micro_emotion in playful_micros:
            return "playful"
        if micro_emotion in celebration_micros:
            return "celebration"

        # Subtext-based fallback
        if "comfort" in subtext.lower() or "seeking" in subtext.lower():
            return "comfort"
        if "venting" in subtext.lower() or "frustration" in subtext.lower():
            return "space"
        if "joy" in subtext.lower() or "celebration" in subtext.lower():
            return "celebration"

        # Default based on valence + arousal
        if valence < -0.2 and arousal > 0.5:
            return "space"
        if valence < -0.2:
            return "comfort"
        if valence > 0.3 and arousal > 0.5:
            return "celebration"
        if valence > 0.3:
            return "playful"
        if arousal < 0.3:
            return "gentle_presence"

        return "comfort"

    @staticmethod
    def _default_mode() -> dict[str, Any]:
        """Return the default response mode."""
        config = dict(RESPONSE_MODES["comfort"])
        config["id"] = "comfort"
        return config

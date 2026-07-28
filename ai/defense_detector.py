"""
Hinata - Defense Mechanism & Coping Style Recognizer

Detects psychological defense mechanisms in user messages, enabling
Hinata to respond with appropriate strategies rather than reacting
to surface-level content.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class DefenseDetector:
    """Recognizes psychological defense mechanisms in user communication."""

    # ── Public API ─────────────────────────────────────────────────

    def detect(
        self,
        message: str,
        *,
        context_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Detect defense mechanisms in a user message.

        Args:
            message: The user's message text.
            context_history: Optional list of recent message/feeling pairs.

        Returns:
            Dict with detected mechanisms, primary mechanism, and strategies.
        """
        msg_lower = message.lower()
        mechanisms: dict[str, float] = {}

        # Run all detectors
        self._check_humor(message, msg_lower, mechanisms)
        self._check_intellectualization(message, msg_lower, mechanisms)
        self._check_topic_change(message, msg_lower, mechanisms, context_history)
        self._check_minimization(message, msg_lower, mechanisms)
        self._check_projection(message, msg_lower, mechanisms)
        self._check_passive_aggression(message, msg_lower, mechanisms)
        self._check_idealization_devaluation(message, msg_lower, mechanisms)

        if not mechanisms:
            return {
                "primary": "none",
                "mechanisms": {},
                "strategy": "respond normally",
            }

        primary = max(mechanisms, key=mechanisms.get)
        strategy = self._get_strategy(primary)

        return {
            "primary": primary,
            "mechanisms": {k: round(v, 2) for k, v in mechanisms.items()},
            "strategy": strategy,
        }

    # ── Detectors ──────────────────────────────────────────────────

    @staticmethod
    def _check_humor(msg: str, msg_lower: str, mechanisms: dict[str, float]) -> None:
        """Detect humor/teasing as deflection from serious topics."""
        score = 0.0
        humor_markers = ["😂", "😄", "lol", "lmao", "hehe", "haha", "jk", "just kidding"]
        serious_topic_markers = ["but", "though", "seriously", "actually", "honestly"]

        has_humor = any(m in msg_lower for m in humor_markers)
        has_serious = any(m in msg_lower for m in serious_topic_markers)

        if has_humor and has_serious:
            score = 0.7
        elif has_humor and len(msg) < 80:
            score = 0.4

        if score > 0:
            mechanisms["humor"] = score

    @staticmethod
    def _check_intellectualization(msg: str, msg_lower: str, mechanisms: dict[str, float]) -> None:
        """Detect over-analysis as avoidance of emotional processing."""
        score = 0.0
        analysis_words = ["logically", "analyze", "perspective", "rationally",
                          "objectively", "theoretically", "statistically"]
        emotion_words = ["feel", "felt", "feeling", "emotion", "emotional"]

        has_analysis = sum(1 for w in analysis_words if w in msg_lower)
        lacks_emotion = not any(w in msg_lower for w in emotion_words)
        is_long = len(msg) > 150

        if has_analysis >= 2 and lacks_emotion and is_long:
            score = 0.7
        elif has_analysis >= 1 and lacks_emotion:
            score = 0.4

        if score > 0:
            mechanisms["intellectualization"] = score

    @staticmethod
    def _check_topic_change(
        msg: str,
        msg_lower: str,
        mechanisms: dict[str, float],
        context: list[dict[str, Any]] | None,
    ) -> None:
        """Detect abrupt topic changes away from emotional subjects."""
        if not context or len(context) < 2:
            return

        # Check if the user's previous message had emotional content
        prev = context[-1] if context else {}
        prev_feeling = prev.get("feeling", {})
        prev_need = prev_feeling.get("need", "")

        if prev_need in ("connection", "security", "significance"):
            # Check if current message changes topic rapidly
            transition_words = ["anyway", "so", "by the way", "on another note",
                                "forget that", "never mind", "different topic"]
            if any(w in msg_lower for w in transition_words):
                mechanisms["topic_change"] = 0.6

    @staticmethod
    def _check_minimization(msg: str, msg_lower: str, mechanisms: dict[str, float]) -> None:
        """Detect downplaying of feelings or experiences."""
        score = 0.0
        minimizers = ["it's nothing", "doesn't matter", "not a big deal",
                       "it's fine", "no biggie", "whatever", "who cares",
                       "not important", "don't worry about it"]

        for phrase in minimizers:
            if phrase in msg_lower:
                score += 0.3

        if score > 0:
            mechanisms["minimization"] = min(score, 1.0)

    @staticmethod
    def _check_projection(msg: str, msg_lower: str, mechanisms: dict[str, float]) -> None:
        """Detect projection — attributing one's own feelings to Hinata."""
        score = 0.0
        projection_patterns = [
            r"\byou\w+ (don't care|don't understand|don't get it|are mad|are upset)\b",
            r"\byou\w+ (think|feel) (i'm|i am) (bad|wrong|stupid)\b",
            r"\byou\w+ (hate|don't like) me\b",
            r"\byou're just (saying|pretending)\b",
        ]
        for pattern in projection_patterns:
            if re.search(pattern, msg_lower):
                score += 0.5

        if score > 0:
            mechanisms["projection"] = min(score, 1.0)

    @staticmethod
    def _check_passive_aggression(msg: str, msg_lower: str, mechanisms: dict[str, float]) -> None:
        """Detect passive-aggressive communication."""
        score = 0.0
        passive_patterns = [
            r"\bfine\b", r"\bwhatever\b", r"\bi guess\b", r"\bif you say so\b",
            r"\bnever mind\b", r"\bdon't worry about it\b",
            r"\bi'm (fine|ok|okay)\b", r"\bit's nothing\b",
        ]
        # High score if short + passive markers + negative context
        matches = sum(1 for p in passive_patterns if re.search(p, msg_lower))
        is_short = len(msg) < 60

        if matches >= 2 and is_short:
            score = 0.6
        elif matches >= 1 and is_short:
            score = 0.3

        if score > 0:
            mechanisms["passive_aggression"] = score

    @staticmethod
    def _check_idealization_devaluation(msg: str, msg_lower: str, mechanisms: dict[str, float]) -> None:
        """Detect extreme praise followed by criticism — fearul-avoidant pattern."""
        has_extreme_praise = any(w in msg_lower for w in [
            "you're the best", "perfect", "amazing", "incredible",
            "you're so good", "i love you so much",
        ])
        has_criticism = any(w in msg_lower for w in [
            "but", "however", "except", "although", "still",
            "you don't", "you never", "you always",
        ])
        if has_extreme_praise and has_criticism:
            mechanisms["idealization_devaluation"] = 0.8

    # ── Strategy mapping ───────────────────────────────────────────

    @staticmethod
    def _get_strategy(mechanism: str) -> str:
        """Return the recommended Hinata strategy for a given defense."""
        strategies = {
            "humor": "gentle: 'I know you're joking, but I'm here if you need'",
            "intellectualization": "meet at intellectual level first, then gently invite feelings",
            "topic_change": "note the avoided topic, revisit when trust is higher",
            "minimization": "validate anyway: 'It's okay to feel small things too'",
            "projection": "don't take personally, reflect gently",
            "passive_aggression": "extra patience, don't react to bait",
            "idealization_devaluation": "steady, consistent, no drama cycle",
        }
        return strategies.get(mechanism, "respond with warmth and patience")

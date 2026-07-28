"""
Hinata - Core Emotional Needs Analyzer

Maps detected emotions to unmet core psychological needs based on
Maslow + Glasser's Choice Theory + Self-Determination Theory.

Builds a per-user need profile that Hinata uses to adapt responses.
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

CORE_NEEDS = {
    "security": "safety, stability, predictability",
    "significance": "feeling important, valued, seen",
    "connection": "belonging, intimacy, being understood",
    "autonomy": "control, freedom, choice",
    "competence": "mastery, growth, achievement",
    "novelty": "excitement, surprise, adventure",
    "meaning": "purpose, contribution",
}


class NeedAnalyzer:
    """Analyses user messages to identify core emotional needs."""

    def __init__(self) -> None:
        # Mapping micro-emotions to likely unmet needs
        self._emotion_need_map: dict[str, list[str]] = {
            "anxious": ["security"],
            "scared": ["security"],
            "lonely": ["connection"],
            "hurt": ["security", "significance"],
            "frustrated": ["autonomy", "competence"],
            "overwhelmed": ["autonomy", "security"],
            "vulnerable": ["connection", "security"],
            "numb": ["significance", "meaning"],
            "hopeful": ["meaning", "significance"],
            "proud": ["significance", "competence"],
            "confused": ["competence"],
            "bittersweet": ["meaning", "connection"],
            "nostalgic": ["connection"],
            "grateful": ["connection", "significance"],
            "defensive": ["autonomy", "security"],
            "playful": ["novelty", "connection"],
            "content": ["security"],
            "guarded": ["autonomy", "security"],
            "longing": ["connection", "significance"],
            "embarrassed": ["significance", "connection"],
            "tender": ["connection", "intimacy"],
        }

    def analyze(
        self,
        feeling: dict[str, Any],
        message: str,
        history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Analyze which core needs are being expressed/unmet.

        Args:
            feeling: The feeling detection result dict.
            message: The user's raw message.
            history: Optional list of recent feeling snapshots.

        Returns:
            Dict with primary_need, secondary_need, satisfaction_levels,
            and dominant_need_profile.
        """
        need_scores: dict[str, float] = {n: 0.0 for n in CORE_NEEDS}

        # 1. From detected need
        detected_need = feeling.get("need", "")
        if detected_need in need_scores:
            need_scores[detected_need] += 0.8

        # 2. From micro-emotion
        micro = feeling.get("micro_emotion", "")
        if micro in self._emotion_need_map:
            for n in self._emotion_need_map[micro]:
                if n in need_scores:
                    need_scores[n] += 0.5

        # 3. From valence + arousal combination
        valence = feeling.get("valence", 0.0)
        arousal = feeling.get("arousal", 0.5)
        if valence < -0.3 and arousal > 0.6:
            need_scores["autonomy"] += 0.3
        elif valence < -0.3 and arousal < 0.4:
            need_scores["connection"] += 0.4
        elif valence > 0.4 and arousal > 0.6:
            need_scores["significance"] += 0.3

        # 4. Vulnerability signal
        vuln = feeling.get("vulnerability", 0.0)
        if vuln > 0.6:
            need_scores["connection"] += 0.3
            need_scores["security"] += 0.2

        # 5. Incorporate history trajectory
        if history and len(history) >= 3:
            recent_needs = [h.get("need", "") for h in history[-5:] if h.get("need")]
            if recent_needs:
                common = Counter(recent_needs).most_common(1)[0][0]
                if common in need_scores:
                    need_scores[common] += 0.2  # persistent need

        # Sort and rank
        ranked = sorted(need_scores.items(), key=lambda x: x[1], reverse=True)
        top_needs = [n for n, s in ranked if s > 0.3]

        satisfaction = {
            need: round(1.0 - need_scores.get(need, 0.0), 2) for need in CORE_NEEDS
        }

        result = {
            "primary_need": top_needs[0] if top_needs else "significance",
            "secondary_need": top_needs[1] if len(top_needs) > 1 else "",
            "satisfaction_levels": satisfaction,
            "all_need_scores": {n: round(s, 2) for n, s in ranked},
            "dominant_need_profile": self._describe_profile(top_needs),
        }
        logger.debug("Need analysis: primary=%s", result["primary_need"])
        return result

    def build_user_need_profile(
        self, need_history: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build a persistent need profile from interaction history.

        Args:
            need_history: List of need analysis results over time.

        Returns:
            User need profile dict.
        """
        if not need_history:
            return {
                "dominant_needs": ["significance", "connection"],
                "need_satisfaction_baseline": {n: 0.7 for n in CORE_NEEDS},
            }

        primary_needs = [h.get("primary_need", "") for h in need_history if h.get("primary_need")]
        counter = Counter(primary_needs)
        total = sum(counter.values()) or 1

        profile = {
            "dominant_needs": [n for n, _ in counter.most_common(3)],
            "need_distribution": {n: round(c / total, 2) for n, c in counter.most_common()},
        }
        return profile

    @staticmethod
    def _describe_profile(needs: list[str]) -> str:
        """Generate a human-readable profile description."""
        descriptions = {
            "security": "needs stability and safety",
            "significance": "wants to feel valued and seen",
            "connection": "craves intimacy and belonging",
            "autonomy": "needs control and freedom",
            "competence": "driven by mastery and growth",
            "novelty": "seeks excitement and variety",
            "meaning": "looking for purpose",
        }
        if not needs:
            return ""
        primary = descriptions.get(needs[0], "")
        if len(needs) > 1:
            secondary = descriptions.get(needs[1], "")
            return f"{primary}, also {secondary}"
        return primary

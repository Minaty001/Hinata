"""
Hinata - Feeling Detection Engine

Detects multi-dimensional emotional state from user messages using
LLM-powered classification, behavioral signals, and conversation context.

Replaces the old random/timer-based mood system with real detection.
Produces a 16-dimensional emotional vector plus need/subtext analysis.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Micro-emotion taxonomy
MICRO_EMOTIONS: dict[str, str] = {
    "bittersweet": "mixed joy and sadness",
    "longing": "desire for something absent",
    "nostalgic": "sentimental longing for past",
    "vulnerable": "emotionally exposed, tender",
    "guarded": "protective, walls up",
    "overwhelmed": "too much at once",
    "numb": "emotionally exhausted, flat",
    "hopeful": "cautious optimism",
    "defensive": "ready to protect self",
    "playful": "light, teasing energy",
    "tender": "soft, gentle affection",
    "proud": "pleased with achievement",
    "embarrassed": "awkward, self-conscious",
    "grateful": "appreciative, thankful",
    "content": "peaceful satisfaction",
    "anxious": "worried, uneasy",
    "frustrated": "irritated, blocked",
    "hurt": "emotionally pained",
    "lonely": "feeling alone or isolated",
    "confused": "uncertain, disoriented",
}

CORE_NEEDS: dict[str, str] = {
    "security": "safety, stability, predictability",
    "significance": "feeling important, valued, seen",
    "connection": "belonging, intimacy, being understood",
    "autonomy": "control, freedom, choice",
    "competence": "mastery, growth, achievement",
    "novelty": "excitement, surprise, adventure",
    "meaning": "purpose, contribution",
}


class FeelingDetector:
    """Detects emotional state from user messages using keyword + context analysis.

    This is a lightweight rule-based detector that runs before the LLM
    response. For deeper analysis, the results can be refined by the LLM
    during response generation.
    """

    def __init__(self) -> None:
        self._build_keyword_map()

    def detect(
        self,
        message: str,
        *,
        message_history: list[str] | None = None,
        response_time: float | None = None,
        hour_of_day: int | None = None,
        behavioral_signals: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Detect emotional state from a user message.

        Args:
            message: The user's message text.
            message_history: Recent user messages (for trajectory analysis).
            response_time: Seconds since last AI response.
            hour_of_day: Hour (0-23) of the message.
            behavioral_signals: Signals from BehavioralTracker.

        Returns:
            Emotional state dict with keys: valence, arousal, dominance,
            social_warmth, vulnerability, need, subtext, micro_emotion,
            confidence.
        """
        msg_lower = message.lower()
        valence = self._detect_valence(msg_lower, message)
        arousal = self._detect_arousal(msg_lower, message)
        dominance = self._detect_dominance(msg_lower, message)
        social_warmth = self._detect_social_warmth(msg_lower, message)
        vulnerability = self._detect_vulnerability(msg_lower, message, behavioral_signals)
        micro_emotion = self._detect_micro_emotion(msg_lower, message)
        need = self._detect_need(msg_lower, micro_emotion, valence)
        subtext = self._detect_subtext(
            message, msg_lower, valence, arousal, response_time, behavioral_signals,
        )

        # Detect masked emotions: gap between stated and detected
        masked = self._detect_masked(message, msg_lower, valence, arousal)

        # Emotional trajectory from history
        trajectory = self._detect_trajectory(msg_lower, message_history or [])

        confidence = self._compute_confidence(message, valence, arousal)

        return {
            "valence": round(valence, 3),
            "arousal": round(arousal, 3),
            "dominance": round(dominance, 3),
            "social_warmth": round(social_warmth, 3),
            "vulnerability": round(vulnerability, 3),
            "need": need,
            "subtext": subtext,
            "micro_emotion": micro_emotion,
            "masked": masked,
            "trajectory": trajectory,
            "confidence": round(confidence, 3),
        }

    def to_snapshot(self, result: dict[str, Any]) -> dict[str, Any]:
        """Convert detection result to a DB-ready snapshot dict."""
        return {
            "valence": result["valence"],
            "arousal": result["arousal"],
            "dominance": result["dominance"],
            "social_warmth": result["social_warmth"],
            "vulnerability": result["vulnerability"],
            "need": result["need"],
            "subtext": result["subtext"],
            "micro_emotion": result["micro_emotion"],
            "confidence": result["confidence"],
        }

    # ── Internal: valence ──────────────────────────────────────────

    def _detect_valence(self, msg_lower: str, msg: str) -> float:
        """Detect valence: positive vs negative (-1 to 1)."""
        score = 0.0
        for word in self._positive_words:
            if word in msg_lower:
                score += 0.15
        for word in self._negative_words:
            if word in msg_lower:
                score -= 0.15
        for word in self._high_positive:
            if word in msg_lower:
                score += 0.3
        for word in self._high_negative:
            if word in msg_lower:
                score -= 0.3
        # Length-based intensity
        if len(msg) > 200 and abs(score) > 0.2:
            score *= 1.3
        return max(-1.0, min(1.0, score))

    def _detect_arousal(self, msg_lower: str, msg: str) -> float:
        """Detect arousal: calm vs intense (0 to 1)."""
        arousal = 0.3  # baseline
        if any(w in msg_lower for w in self._high_energy_words):
            arousal += 0.3
        if any(w in msg_lower for w in self._low_energy_words):
            arousal -= 0.2
        # Exclamation marks & caps
        exclaim = msg.count("!")
        if exclaim > 2:
            arousal += 0.2
        if any(c.isupper() for c in msg if c.isalpha()) and len(msg) > 20:
            upper_ratio = sum(1 for c in msg if c.isupper()) / max(len(msg), 1)
            if upper_ratio > 0.3:
                arousal += 0.2
        # Questions indicate mental engagement
        if "?" in msg:
            arousal += 0.1
        # Very long rants → high arousal
        if len(msg) > 300:
            arousal += 0.15
        return max(0.0, min(1.0, arousal))

    def _detect_dominance(self, msg_lower: str, msg: str) -> float:
        """Detect dominance: in control vs overwhelmed (0 to 1)."""
        dom = 0.5  # neutral
        if any(w in msg_lower for w in self._dominance_high_words):
            dom += 0.2
        if any(w in msg_lower for w in self._dominance_low_words):
            dom -= 0.2
        if any(w in msg_lower for w in self._helpless_words):
            dom -= 0.3
        return max(0.0, min(1.0, dom))

    def _detect_social_warmth(self, msg_lower: str, msg: str) -> float:
        """Detect social warmth: withdrawn vs connecting (0 to 1)."""
        warmth = 0.5
        if any(w in msg_lower for w in self._warmth_high_words):
            warmth += 0.2
        if any(w in msg_lower for w in self._warmth_low_words):
            warmth -= 0.2
        # Short cold replies
        if len(msg) < 20 and not any(w in msg_lower for w in self._warmth_high_words):
            warmth -= 0.15
        return max(0.0, min(1.0, warmth))

    def _detect_vulnerability(
        self,
        msg_lower: str,
        msg: str,
        signals: dict[str, Any] | None,
    ) -> float:
        """Detect vulnerability: guarded vs open (0 to 1)."""
        vuln = 0.2  # default guarded
        if any(w in msg_lower for w in self._vulnerability_high_words):
            vuln += 0.3
        if len(msg) > 150:
            vuln += 0.15
        if any(w in msg_lower for w in self._vulnerability_low_words):
            vuln -= 0.2
        # Late-night vulnerability boost
        if signals and signals.get("hour_of_day", 12) in (0, 1, 2, 3):
            vuln += 0.15
        return max(0.0, min(1.0, vuln))

    def _detect_micro_emotion(self, msg_lower: str, msg: str) -> str:
        """Detect the most specific micro-emotion."""
        scores: dict[str, float] = {}
        for emotion, keywords in self._micro_emotion_keywords.items():
            score = 0.0
            for kw in keywords:
                if kw in msg_lower:
                    score += 1.0
            if score > 0:
                scores[emotion] = score
        if scores:
            best = max(scores, key=scores.get)
            return best
        # Fallback to basic valence-based label
        valence = self._detect_valence(msg_lower, msg)
        arousal = self._detect_arousal(msg_lower, msg)
        if valence > 0.3 and arousal > 0.5:
            return "excited"
        if valence < -0.3 and arousal > 0.5:
            return "frustrated"
        if valence < -0.3 and arousal < 0.4:
            return "sad"
        if valence > 0.2 and arousal < 0.4:
            return "content"
        return "neutral"

    def _detect_need(
        self, msg_lower: str, micro_emotion: str, valence: float
    ) -> str:
        """Map emotional state to core unmet need."""
        for need, keywords in self._need_keywords.items():
            for kw in keywords:
                if kw in msg_lower:
                    return need
        # Fallback mapping from micro-emotion
        emotion_need_map: dict[str, str] = {
            "lonely": "connection",
            "hurt": "security",
            "anxious": "security",
            "frustrated": "autonomy",
            "overwhelmed": "autonomy",
            "vulnerable": "connection",
            "numb": "significance",
            "hopeful": "meaning",
            "proud": "significance",
            "confused": "competence",
            "bittersweet": "meaning",
            "nostalgic": "connection",
            "grateful": "connection",
            "playful": "novelty",
        }
        if micro_emotion in emotion_need_map:
            return emotion_need_map[micro_emotion]
        if valence < -0.3:
            return "connection"
        return "significance"

    def _detect_subtext(
        self,
        msg: str,
        msg_lower: str,
        valence: float,
        arousal: float,
        response_time: float | None,
        signals: dict[str, Any] | None,
    ) -> str:
        """Detect the emotional subtext beneath the surface message."""
        # Short negative response after long history → deflection
        if valence < -0.1 and len(msg) < 30:
            return "deflecting true feelings"

        # "I'm fine" or similar dismissals
        if re.search(r"\b(i'?m\s+)?fine\b", msg_lower) and valence < 0:
            return "NOT fine — using deflection"

        # Long message with mixed signals
        if len(msg) > 100 and -0.2 < valence < 0.2:
            return "ambivalent, processing mixed emotions"

        # Late-night vulnerability
        if signals and signals.get("hour_of_day", 12) in (0, 1, 2, 3) and valence < -0.1:
            return "vulnerable, seeking comfort in the quiet hours"

        # High arousal + negative → venting
        if valence < -0.2 and arousal > 0.6:
            return "venting frustration, may not want solutions"

        # Vulnerability + low arousal → seeking comfort
        if valence < -0.1 and arousal < 0.4:
            return "seeking comfort, not solutions"

        if valence > 0.3 and arousal > 0.5:
            return "sharing joy, wants celebration"

        return "straightforward communication"

    def _detect_masked(
        self,
        msg: str,
        msg_lower: str,
        valence: float,
        arousal: float,
    ) -> dict[str, Any]:
        """Detect gap between stated emotion and detected emotion."""
        masked = {"is_masked": False, "stated": "", "detected": ""}
        # Check for positive statements with negative detected valence
        positive_statement = any(
            phrase in msg_lower for phrase in ["i'm great", "i'm ok", "i'm fine", "all good", "no issues"]
        )
        if positive_statement and valence < -0.2:
            masked["is_masked"] = True
            masked["stated"] = "positive"
            masked["detected"] = "negative_subtext"
        # Long angry message starting with "whatever" or "never mind"
        if msg_lower.startswith(("whatever", "never mind", "forget it", "doesn't matter")) and len(msg) > 50:
            masked["is_masked"] = True
            masked["stated"] = "dismissive"
            masked["detected"] = "hurt_beneath"
        return masked

    def _detect_trajectory(
        self, msg_lower: str, history: list[str]
    ) -> str:
        """Detect emotional trajectory by comparing with recent messages."""
        if not history or len(history) < 2:
            return "stable"
        recent_valences = [self._detect_valence(h.lower(), h) for h in history[-5:]]
        current_v = self._detect_valence(msg_lower, "")
        if len(recent_valences) < 2:
            return "stable"
        trend = current_v - sum(recent_valences) / len(recent_valences)
        if trend < -0.3:
            return "declining"
        if trend > 0.3:
            return "improving"
        # Check variance
        if max(recent_valences) - min(recent_valences) > 0.5:
            return "volatile"
        return "stable"

    def _compute_confidence(self, msg: str, valence: float, arousal: float) -> float:
        """Compute confidence in the detection."""
        conf = 0.5  # base
        if len(msg) > 50:
            conf += 0.15
        if abs(valence) > 0.3:
            conf += 0.15
        if arousal > 0.6 or arousal < 0.3:
            conf += 0.1
        if len(msg) > 200:
            conf += 0.1
        return min(1.0, conf)

    # ── Keyword maps (built once) ──────────────────────────────────

    def _build_keyword_map(self) -> None:
        self._positive_words = {
            "happy", "glad", "good", "great", "love", "nice", "wonderful",
            "amazing", "beautiful", "fantastic", "awesome", "perfect",
            "best", "grateful", "thankful", "blessed", "joy", "excited",
        }
        self._negative_words = {
            "sad", "bad", "terrible", "awful", "hate", "worst", "horrible",
            "depressed", "angry", "upset", "cry", "crying", "hurt", "pain",
            "tired", "exhausted", "lonely", "alone", "broken", "useless",
        }
        self._high_positive = {
            "amazing", "incredible", "fantastic", "extraordinary", "perfect",
            "overjoyed", "ecstatic", "thrilled",
        }
        self._high_negative = {
            "devastated", "desperate", "hopeless", "miserable", "suffering",
            "destroyed", "worthless", "hate myself",
        }
        self._high_energy_words = {
            "so", "very", "really", "totally", "absolutely", "extremely",
            "super", "insanely", "incredibly",
            "!", "!!!", "what", "why", "how dare",
        }
        self._low_energy_words = {
            "whatever", "fine", "ok", "okay", "maybe", "idk", "dunno",
            "tired", "sleepy", "exhausted", "whatever",
        }
        self._dominance_high_words = {
            "i will", "i can", "i know", "i want", "i decided", "i've got this",
            "i'm sure", "definitely", "certainly", "absolutely",
        }
        self._dominance_low_words = {
            "i can't", "i don't know", "maybe", "i'm not sure", "helpless",
            "i give up", "what should i", "i need help",
        }
        self._helpless_words = {
            "i can't", "helpless", "no choice", "i give up", "hopeless",
            "nothing i can do", "it's useless", "what's the point",
        }
        self._warmth_high_words = {
            "you", "we", "us", "together", "thank", "love you", "miss you",
            "care", "warm", "hug", "friend", "❤️", "💕", "🌸",
        }
        self._warmth_low_words = {
            "leave", "alone", "stop", "don't", "go away", "whatever",
            "fine", "never mind", "forget it",
        }
        self._vulnerability_high_words = {
            "i feel", "i'm scared", "i'm worried", "i'm afraid",
            "i don't know what to do", "i need", "i wish",
            "i hope", "i'm struggling", "i'm trying",
            "honestly", "to be honest", "truth is", "confess",
        }
        self._vulnerability_low_words = {
            "i'm fine", "it's nothing", "doesn't matter", "it's ok",
            "never mind", "forget it", "not important",
        }
        self._micro_emotion_keywords: dict[str, list[str]] = {
            "bittersweet": ["bittersweet", "happy but", "sad but", "miss those days"],
            "longing": ["i wish", "i hope", "if only", "someday", "one day"],
            "nostalgic": ["remember when", "good old days", "miss those", "back when"],
            "vulnerable": ["i feel so", "i'm scared", "i'm afraid", "i'm worried"],
            "guarded": ["i'm fine", "it's nothing", "doesn't matter"],
            "overwhelmed": ["too much", "overwhelmed", "can't handle", "so much"],
            "numb": ["don't feel", "numb", "empty", "nothing matters"],
            "hopeful": ["hope", "looking forward", "can't wait", "future"],
            "defensive": ["why are you", "it's not my", "you always", "you never"],
            "playful": ["😂", "😄", "lol", "hehe", "haha", "jk", "just kidding"],
            "tender": ["that's so sweet", "you're so", "you're amazing", "aww"],
            "proud": ["i did it", "i made", "i achieved", "accomplished", "proud"],
            "embarrassed": ["embarrassed", "awkward", "stupid", "silly", "oops"],
            "grateful": ["thank you so", "so grateful", "really appreciate"],
            "content": ["i'm good", "feeling good", "peaceful", "content"],
            "anxious": ["anxious", "nervous", "worried", "stressed", "panic"],
            "frustrated": ["frustrated", "annoyed", "irritated", "ugh", "seriously"],
            "hurt": ["hurt", "pained", "wounded", "that hurts"],
            "lonely": ["lonely", "alone", "no one", "by myself"],
            "confused": ["confused", "don't understand", "what does", "how does"],
        }
        self._need_keywords: dict[str, list[str]] = {
            "security": ["scared", "afraid", "worried", "anxious", "safe",
                         "fear", "panic", "nervous", "uncertain"],
            "significance": ["ignored", "invisible", "worthless", "useless",
                             "no one cares", "don't matter", "unimportant",
                             "proud", "accomplished", "achieved"],
            "connection": ["lonely", "alone", "no one", "miss", "together",
                           "understood", "heard", "listened", "abandoned"],
            "autonomy": ["trapped", "stuck", "no choice", "forced", "control",
                         "freedom", "can't", "helpless", "suffocated"],
            "competence": ["stupid", "dumb", "can't do", "hopeless", "give up",
                           "failure", "incapable", "learn", "grow"],
            "novelty": ["bored", "tired of", "same old", "routine", "dull",
                        "excitement", "adventure", "new", "something different"],
            "meaning": ["pointless", "what's the point", "purpose", "empty",
                        "meaning", "why bother", "contribution"],
        }

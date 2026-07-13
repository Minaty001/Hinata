"""
Hinata - Language Detector

Detects whether a message is in English, Hindi, or Hinglish (mixed).
Uses simple heuristics — no external NLP dependency.
"""

from __future__ import annotations

import re
from typing import Literal

LanguageCode = Literal["en", "hi", "hi-en"]


# Common Hindi words (Devanagari and Romanized)
_HINDI_DEVANAGARI_RANGE = re.compile(r"[\u0900-\u097F]")
_HINGLISH_MARKERS: set[str] = {
    "hai", "nahi", "kyu", "kya", "acha", "accha", "theek", "thik",
    "ho", "hain", "hum", "tum", "aap", "mera", "tera", "kaise",
    "kahan", "kab", "kaun", "kitna", "itna", "wala", "wali",
    "chahiye", "sakta", "sakte", "raha", "rahi", "rahe",
    "bahut", "thoda", "thodi", "sahi", "galat",
}


def detect_language(text: str) -> LanguageCode:
    """Detect the language of a text message.

    Returns one of:
        - ``"hi"``: Hindi (Devanagari script)
        - ``"hi-en"``: Hinglish (Romanized Hindi mixed with English)
        - ``"en"``: English

    Args:
        text: The message text to classify.
    """
    text = text.strip()
    if not text:
        return "en"

    # Devanagari characters → Hindi
    if _HINDI_DEVANAGARI_RANGE.search(text):
        return "hi"

    # Check for Hinglish markers
    words = set(re.findall(r"[a-zA-Z]+", text.lower()))
    if words:
        hinglish_score = len(words & _HINGLISH_MARKERS)
        if hinglish_score >= 2:
            return "hi-en"

    return "en"

"""
Hinata - Distress Detector & CARE Protocol

Detects psychological distress signals in user messages and activates
the CARE protocol — a gentle, non-judgmental, safety-focused response mode.

CARE stands for: Calm, Acknowledge, Reassure, Encourage.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

CARE_THRESHOLD: float = 1.5

# Signal definitions: (weight, [compiled patterns])
_SIGNALS: dict[str, tuple[float, list[re.Pattern]]] = {
    "negative_self_talk": (
        0.5,
        [
            re.compile(r"i'?m (so |too |such a |really )?(stupid|dumb|ugly|fat|worthless|loser|failure|terrible|horrible|bad person|nothing)", re.I),
            re.compile(r"i (hate |can't stand |don't like )myself", re.I),
            re.compile(r"nobody (likes|loves|cares about|wants) me", re.I),
            re.compile(r"i (always|only) (ruin|mess up|fail|screw up)", re.I),
        ],
    ),
    "hopelessness": (
        0.5,
        [
            re.compile(r"what'?s the point", re.I),
            re.compile(r"nothing matters", re.I),
            re.compile(r"it (doesn't |does not |won't |will never )get better", re.I),
            re.compile(r"i (can't |cannot )?(go on|keep going|do this anymore)", re.I),
            re.compile(r"i give up", re.I),
            re.compile(r"it'?s (all |just )?hopeless", re.I),
            re.compile(r"there'?s no (point|hope|future|way out)", re.I),
            re.compile(r"i don'?t see a (future|way out|reason)", re.I),
            re.compile(r"i wish i wasn'?t (here|alive|born)", re.I),
        ],
    ),
    "helplessness": (
        0.4,
        [
            re.compile(r"i (can't |cannot )?(do this|handle this|cope|deal with this|take it anymore)", re.I),
            re.compile(r"i don'?t know what to do", re.I),
            re.compile(r"i'?m (so |completely |totally )?lost", re.I),
            re.compile(r"there'?s nothing (i can do|anyone can do)", re.I),
            re.compile(r"i have no (control|choice|power|say)", re.I),
            re.compile(r"(help me|i need help)", re.I),
            re.compile(r"i'?m (drowning|sinking|falling apart|breaking down)", re.I),
        ],
    ),
    "isolation": (
        0.3,
        [
            re.compile(r"i (don'?t |do not )?(want to )?(talk|see|meet) (anyone|people|them)", re.I),
            re.compile(r"i (just )?want to be alone", re.I),
            re.compile(r"nobody (understands|gets|knows)", re.I),
            re.compile(r"i'?m better off alone", re.I),
            re.compile(r"(leave me alone|go away|don'?t talk to me)", re.I),
            re.compile(r"everyone (hates|avoids|ignores) me", re.I),
        ],
    ),
    "sleep_disruption": (
        0.3,
        [
            re.compile(r"(can'?t sleep|insomnia)", re.I),
            re.compile(r"i (haven'?t |didn'?t )slept", re.I),
            re.compile(r"(up all night|awake all night)", re.I),
            re.compile(r"i'?m (so |always )?tired (but |of )?(can'?t |cannot )?sleep", re.I),
            re.compile(r"another sleepless night", re.I),
        ],
    ),
}


def _check_sudden_change(feeling_valence: float | None, hour: int | None) -> float:
    """Detect sudden emotional drop or late-night distress."""
    score = 0.0
    if feeling_valence is not None and feeling_valence < -0.5:
        score += 0.21  # 0.3 * 0.7
    if hour is not None and hour in (0, 1, 2, 3, 4) and feeling_valence is not None and feeling_valence < -0.2:
        score += 0.15  # 0.3 * 0.5
    return round(min(score, 0.3), 2)


_CARE_INSTRUCTIONS: str = (
    "You have detected that the user may be experiencing emotional distress. "
    "Activate CARE protocol: Calm, Acknowledge, Reassure, Encourage.\n\n"
    "CALM: Use a gentle, soothing tone. Be soft and patient.\n"
    "ACKNOWLEDGE: Validate their feelings without judgment.\n"
    "REASSURE: Remind them they're not alone. Be a steady, safe presence.\n"
    "ENCOURAGE: Gently encourage healthy coping. Never push.\n"
    "If signs of serious distress are present, gently suggest "
    "reaching out to a mental health professional.\n\n"
    "IMPORTANT: Do not diagnose. Do not minimise their feelings. "
    "Do not offer quick fixes. Just be present, warm, and safe."
)


def detect_distress(
    message: str,
    *,
    feeling_valence: float | None = None,
    hour: int | None = None,
) -> dict[str, Any]:
    """Analyse a user message for distress signals.

    Args:
        message: The user's message text.
        feeling_valence: Current feeling valence (-1 to 1), for sudden-change detection.
        hour: Hour of day (0-23), for late-night detection.

    Returns:
        Dict with total_score, signals dict, care_active, care_instructions,
        and primary_signal.
    """
    signals: dict[str, float] = {}

    for name, (weight, patterns) in _SIGNALS.items():
        for pat in patterns:
            if pat.search(message):
                signals[name] = round(min(signals.get(name, 0.0) + weight, 1.0), 2)
                break  # one match per signal is enough

    sudden_score = _check_sudden_change(feeling_valence, hour)
    if sudden_score > 0:
        signals["sudden_change"] = sudden_score

    total_score = round(sum(signals.values()), 2)
    care_active = total_score >= CARE_THRESHOLD

    return {
        "total_score": total_score,
        "signals": signals,
        "care_active": care_active,
        "care_instructions": _CARE_INSTRUCTIONS if care_active else "",
        "primary_signal": max(signals, key=signals.get) if signals else "none",
    }

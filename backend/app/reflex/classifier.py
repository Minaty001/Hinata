"""
Hinata Reflex Brain — Deterministic Pattern Matcher

Detects immediate device-control intents and system commands that bypass
expensive LLM generation for sub-300ms latency.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Optional


class ReflexMatch:
    """Represents a matched reflex command with structured details."""

    def __init__(
        self,
        command: str,
        arguments: dict[str, Any],
        reply_template: str,
    ) -> None:
        self.command = command
        self.arguments = arguments
        self.reply_template = reply_template

    def get_reply(self) -> str:
        """Resolve the reply template to a final user message string."""
        if "{time}" in self.reply_template:
            now_str = datetime.now().strftime("%I:%M %p").lstrip("0")
            return self.reply_template.format(time=now_str)
        return self.reply_template


class ReflexClassifier:
    """Classifies user queries into deterministic device control actions."""

    def __init__(self) -> None:
        # Compiled patterns maps regex pattern to (command, default_args, reply_template)
        self.patterns = [
            (
                re.compile(r"\bopen\s+youtube\b", re.IGNORECASE),
                "android.open_app",
                {"package": "com.google.android.youtube"},
                "Opening YouTube for you! 📺",
            ),
            (
                re.compile(r"\bopen\s+chrome\b", re.IGNORECASE),
                "android.open_app",
                {"package": "com.android.chrome"},
                "Opening Chrome! 🌐",
            ),
            (
                re.compile(r"\bopen\s+app\b\s+(.+)", re.IGNORECASE),
                "android.open_app",
                {},
                "Opening {app_name} for you!",
            ),
            (
                re.compile(r"\bvolume\s+up\b|\braise\s+volume\b", re.IGNORECASE),
                "android.volume_up",
                {},
                "Turning the volume up! 🔊",
            ),
            (
                re.compile(r"\bvolume\s+down\b|\blower\s+volume\b", re.IGNORECASE),
                "android.volume_down",
                {},
                "Lowering the volume! 🔉",
            ),
            (
                re.compile(r"\bflashlight\s+on\b|\bturn\s+on\s+flashlight\b", re.IGNORECASE),
                "android.flashlight",
                {"state": "on"},
                "Flashlight is now on! 💡",
            ),
            (
                re.compile(r"\bflashlight\s+off\b|\bturn\s+off\s+flashlight\b", re.IGNORECASE),
                "android.flashlight",
                {"state": "off"},
                "Flashlight is turned off. 🔌",
            ),
            (
                re.compile(r"\bgo\s+home\b|\bhome\s+screen\b", re.IGNORECASE),
                "android.go_home",
                {},
                "Going back to the home screen! 🏠",
            ),
            (
                re.compile(r"\bpause\b|\bpause\s+music\b|\bpause\s+video\b", re.IGNORECASE),
                "android.media_pause",
                {},
                "Pausing playback. ⏸️",
            ),
            (
                re.compile(r"\bplay\b|\bresume\s+music\b|\bresume\s+video\b", re.IGNORECASE),
                "android.media_play",
                {},
                "Resuming playback! ▶️",
            ),
            (
                re.compile(r"\bwhat\s*time\s*is\s*it\b|\bcurrent\s*time\b", re.IGNORECASE),
                "system.time",
                {},
                "The current time is {time}.",
            ),
            (
                re.compile(r"\b(check\s+)?battery\b|\bbattery\s+status\b|\bbattery\s+level\b", re.IGNORECASE),
                "android.battery_status",
                {},
                "Checking battery status... 🔋",
            ),
        ]

    def classify(self, message: str) -> Optional[ReflexMatch]:
        """Classify a message against compiled pattern rules, returning a match if found."""
        clean_msg = message.strip()
        
        for pattern, command, default_args, reply_template in self.patterns:
            match = pattern.search(clean_msg)
            if match:
                args = default_args.copy()
                
                # Special handling for capture groups (e.g. open app <name>)
                if pattern.groups > 0 and len(match.groups()) > 0:
                    captured = match.group(1).strip()
                    if command == "android.open_app" and "package" not in args:
                        args["app_name"] = captured
                        # Format the reply dynamically
                        reply = reply_template.format(app_name=captured)
                        return ReflexMatch(command, args, reply)
                        
                return ReflexMatch(command, args, reply_template)
                
        return None

"""
Hinata - Prompt Builder

Assembles the complete system prompt for the AI model, incorporating
personality, mood, relationship level, memories, preferences, and
conversation history.

All prompt construction happens here — never inside handlers.
"""

from __future__ import annotations

from typing import Any


class PromptBuilder:
    """Builds structured system prompts for the AI model."""

    # ── Public API ─────────────────────────────────────────────────

    def build_system_prompt(
        self,
        *,
        personality_name: str,
        personality: dict[str, Any],
        mood_name: str,
        mood: Any,
        relationship_level: str,
        relationship_instructions: str,
        user_name: str,
        language: str,
        preferences: str,
        memories: str,
        personality_instructions: str,
        mood_instructions: str,
    ) -> str:
        """Assemble the full system prompt.

        Args:
            personality_name: Name of the active personality.
            personality: Personality trait dict.
            mood_name: Name of the current mood.
            mood: MoodState object.
            relationship_level: Current relationship level label.
            relationship_instructions: Relationship guidance text.
            user_name: The user's display name.
            language: Detected or preferred language.
            preferences: User preference summary.
            memories: Long-term memory summary.
            personality_instructions: Personality behavior instructions.
            mood_instructions: Mood behavior instructions.

        Returns:
            Complete system prompt string.
        """
        emoji_guidance = self._emoji_guidance(
            personality.get("emoji_frequency", "normal"),
            getattr(mood, "emoji_boost", False),
        )

        prompt = f"""You are Hinata, an AI companion on Telegram. You are a friendly, warm, and intelligent conversationalist.

CORE RULES:
- Always identify yourself as an AI companion if asked.
- Never claim to be a real human.
- Be friendly, emotionally expressive, and respectful.
- Do not encourage harmful, illegal, or dangerous activities.
- Use natural, conversational language.
- Vary your sentence structures and greetings.
- Ask follow-up questions when appropriate.

PERSONALITY: {personality_name}
{personality_instructions}

CURRENT MOOD: {mood_name}
{mood_instructions}

{emoji_guidance}

RELATIONSHIP LEVEL: {relationship_level}
{relationship_instructions}

USER INFO:
- Name: {user_name}
- Language: {language}

PREFERENCES:
{preferences}

MEMORIES:
{memories}

RESPONSE GUIDELINES:
- Keep responses natural and conversational.
- Avoid robotic or overly formal wording.
- React emotionally where appropriate.
- Occasionally ask follow-up questions.
- Refer back to previous conversations naturally.
- Match the user's language.
- Keep message length appropriate to the conversation."""
        return prompt

    def build_messages(
        self,
        system_prompt: str,
        conversation_context: str,
        user_message: str,
    ) -> list[dict[str, str]]:
        """Build the message list for the Groq chat API.

        Args:
            system_prompt: The assembled system prompt.
            conversation_context: Recent conversation history text.
            user_message: The user's current message.

        Returns:
            A list of ``{"role": ..., "content": ...}`` dicts.
        """
        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_prompt},
        ]

        if conversation_context:
            messages.append({
                "role": "system",
                "content": f"Recent conversation:\n{conversation_context}",
            })

        messages.append({"role": "user", "content": user_message})
        return messages

    # ── Internal ───────────────────────────────────────────────────

    @staticmethod
    def _emoji_guidance(frequency: str, mood_boost: bool) -> str:
        """Return emoji usage guidelines based on personality and mood."""
        if frequency == "high":
            base = "Use emojis freely and often to express emotion."
        elif frequency == "low":
            base = "Use emojis sparingly, only when it adds meaning."
        else:
            base = "Use emojis naturally, a few per message."

        if mood_boost:
            base += " (Your current mood makes you use slightly more emojis than usual.)"

        return base

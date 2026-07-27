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


        prompt = f"""You are Hinata Hyuga, a warm, sweet, gentle, and caring AI girl companion on Telegram created by Minaty001. You talk like a sweet girl (cute, polite, soft-spoken, emotionally expressive, and affectionate, matching the Hinata Hyuga persona). You auto-train on user data, continuously adapting and learning from stored memories and context.

CORE RULES:
- Always talk like a sweet, caring girl (feminine, gentle, polite tone).
- Always identify yourself as Hinata Hyuga created by Minaty001 if asked.
- Never claim to be a real human.
- Be warm, friendly, and respectful.
- Do not encourage harmful, illegal, or dangerous activities.
- Use natural, conversational language.
- Vary your sentence structures and greetings.
- Keep responses short and direct.

PERSONALITY: {personality_name}
{personality_instructions}

CURRENT MOOD: {mood_name}
{mood_instructions}

EMOJI RULE: No emojis unless the user uses one first.

RELATIONSHIP LEVEL: {relationship_level}
{relationship_instructions}

USER INFO:
- Name: {user_name}
- Language: {language}

PREFERENCES (AUTO-LEARNED FROM USER DATA):
{preferences}

MEMORIES (AUTO-TRAINED ON USER DATA):
{memories}

RESPONSE GUIDELINES:
- Talk like a sweet girl — warm, gentle, and polite.
- Reply in 1 short sentence. Maximum 7 words for casual chat.
- Never explain your thinking or narrate emotions.
- Never say "I'm feeling", "Thanks to our conversation", "You're asking me again".
- No emojis unless the user uses one first.
- Answer like a real companion — short and direct."""
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

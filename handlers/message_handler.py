"""
Hinata - Message Handler (Next-Level Integration)

Processes incoming text messages through the full next-level AI pipeline:

1. Load/register user profile
2. Feeling detection (multi-dim emotion vector)
3. Need analysis + defense detection
4. Response mode selection (8 modes)
5. Behavioral tracking
6. Store incoming message
7. Retrieve context & memories + vector store similarity
8. Determine personality & relationship
9. Build system prompt (with mode instructions)
10. Model routing (auto-select provider)
11. Call AI
12. Clean & validate response
13. Store AI reply + encode as training sample
14. Update relationship score + dimensions
15. Send response to user
16. Deferred quality scoring (when user's next message arrives)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import telegram

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from telegram import Update
from telegram.ext import ContextTypes

from ai.context_builder import build_conversation_context
from ai.feeling_detector import FeelingDetector
from ai.mood_engine import MoodEngine
from ai.need_analyzer import NeedAnalyzer
from ai.defense_detector import DefenseDetector
from ai.personality_engine import PersonalityEngine
from ai.prompt_builder import PromptBuilder
from ai.relationship_engine import RelationshipEngine
from ai.response_cleaner import clean_response, split_long_message
from ai.response_mode_selector import ResponseModeSelector
from ai.vulnerability_scaffold import get_scaffold_instructions
from ai.distress_detector import detect_distress

from memory.memory_manager import get_memories_summary

from services.chat_service import save_message, get_conversation_history
from services.user_service import get_or_create_user, get_user_preferences

from training.behavioral_tracker import BehavioralTracker
from training.quality_scorer import QualityScorer
from training.conversation_encoder import ConversationEncoder
from training.model_router import ModelRouter

from database.models import (
    FeelingSnapshot,
    RelationshipDimension,
    TrainingSample,
)

from utils.rate_limit import rate_limiter
from utils.validators import sanitise_input

logger = logging.getLogger(__name__)

_MAINTENANCE_MODE_KEY = "maintenance_mode"

# Per-user state for behavioral tracking (keyed by user ID)
_user_message_history: dict[int, dict[str, Any]] = {}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process incoming text messages through the next-level AI pipeline."""
    user_tg = update.effective_user
    message_text = update.message.text.strip()

    if not message_text:
        return

    logger.info("Message from %s: %.50s...", user_tg.id, message_text)

    # ── Maintenance mode check ────────────────────────────────────
    if context.bot_data.get(_MAINTENANCE_MODE_KEY, False):
        from config import settings
        if user_tg.id != settings.OWNER_ID:
            await update.message.reply_text(
                "🌸 Hinata is taking a short break for maintenance. "
                "I'll be back soon!",
            )
            return

    # ── Rate limiter ──────────────────────────────────────────────
    limiter = context.bot_data.get("rate_limiter", rate_limiter)
    if limiter.is_limited(user_tg.id):
        logger.info("Rate-limited user %s.", user_tg.id)
        return

    # ── Sanitise input ────────────────────────────────────────────
    message_text = sanitise_input(message_text)

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing",
    )

    # ── Shared resources ──────────────────────────────────────────
    session_factory: async_sessionmaker[AsyncSession] = context.bot_data["session_factory"]
    personality_engine: PersonalityEngine = context.bot_data["personality_engine"]
    mood_engine: MoodEngine = context.bot_data["mood_engine"]
    relationship_engine: RelationshipEngine = context.bot_data["relationship_engine"]
    prompt_builder: PromptBuilder = context.bot_data["prompt_builder"]
    ai_client = context.bot_data.get("ai_client")

    # Next-level engines (initialised once)
    feeling_detector: FeelingDetector = context.bot_data.get(
        "feeling_detector", FeelingDetector()
    )
    need_analyzer: NeedAnalyzer = context.bot_data.get(
        "need_analyzer", NeedAnalyzer()
    )
    defense_detector: DefenseDetector = context.bot_data.get(
        "defense_detector", DefenseDetector()
    )
    response_selector: ResponseModeSelector = context.bot_data.get(
        "response_selector", ResponseModeSelector()
    )
    behavioral_tracker: BehavioralTracker = context.bot_data.get(
        "behavioral_tracker", BehavioralTracker()
    )
    quality_scorer: QualityScorer = context.bot_data.get(
        "quality_scorer", QualityScorer()
    )
    conversation_encoder: ConversationEncoder = context.bot_data.get(
        "conversation_encoder", ConversationEncoder()
    )
    model_router: ModelRouter = context.bot_data.get(
        "model_router", ModelRouter()
    )
    async with session_factory() as session:
        try:
            # ── 1. Load or create user profile ─────────────────────
            user = await get_or_create_user(
                session,
                telegram_id=user_tg.id,
                username=user_tg.username,
                display_name=user_tg.first_name,
            )

            # ── 2. Deferred quality scoring for previous interaction ─
            # If there's a pending assistant message, score based on user's reply
            prev_state = _user_message_history.get(user.id, {})
            last_assistant_msg = prev_state.get("last_assistant_msg", "")
            if last_assistant_msg:
                score_result = quality_scorer.score_interaction(
                    user_replied=True,
                    user_replied_quickly=(
                        prev_state.get("last_response_time", 999) < 120
                    ),
                    user_expanded_topic=(len(message_text) > len(prev_state.get("prev_msg", "")) + 20),
                    user_showed_affection=any(
                        w in message_text.lower()
                        for w in ["love", "thank", "❤️", "💕", "sweet", "amazing"]
                    ),
                    user_opened_up_more=(len(message_text) > 200),
                    message_length=len(message_text),
                )
                # Update the training sample with quality score
                prev_sample_id = prev_state.get("last_sample_id")
                if prev_sample_id:
                    try:
                        stmt = (
                            select(TrainingSample)
                            .where(TrainingSample.id == prev_sample_id)
                        )

                        result = await session.execute(stmt)
                        sample = result.scalar_one_or_none()
                        if sample:
                            sample.quality_score = score_result["score"]
                            await session.commit()
                    except Exception:
                        pass

            # ── 3. Get conversation context (for feeling + need) ──
            # Fetch history BEFORE saving this turn so context/trajectory exclude it
            conversation_context = await build_conversation_context(session, user.id)

            # ── 4. Get recent messages for trajectory ──────────────
            recent_msgs = await get_conversation_history(session, user.id, limit=10)
            recent_user_msgs = [
                m.message for m in recent_msgs if m.role == "user"
            ]

            # Persist user message (was missing — broke multi-turn memory)
            await save_message(session, user.id, "user", message_text)

            # Compute behavioral signals dynamically
            user_msgs = [m for m in recent_msgs if m.role == "user"]
            message_lengths_recent = [len(m.message) for m in user_msgs]

            response_times_recent = []
            for i in range(1, len(recent_msgs)):
                if recent_msgs[i].role == "user" and recent_msgs[i-1].role == "assistant":
                    dt = (recent_msgs[i].timestamp - recent_msgs[i-1].timestamp).total_seconds()
                    response_times_recent.append(dt)

            import re
            emoji_pattern = re.compile(r"[\u263a-\u263f\u2700-\u27bf\U0001f300-\U0001f9ff]")
            emoji_count_recent = [len(emoji_pattern.findall(m.message)) for m in user_msgs]

            topic_switches_recent = [len(m.message) < 50 for m in user_msgs]
            self_disclosures_recent = [any(w in m.message.lower() for w in ["i feel", "my", "i am", "me", "personally"]) for m in user_msgs]

            import time
            current_time = time.time()
            last_response_time = None
            if recent_msgs and recent_msgs[-1].role == "assistant" and recent_msgs[-1].timestamp:
                ts = recent_msgs[-1].timestamp
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                last_response_time = (datetime.now(timezone.utc) - ts).total_seconds()

            computed_signals = behavioral_tracker.compute_signals(
                current_time=current_time,
                last_response_time=last_response_time,
                message_length=len(message_text),
                message_lengths_recent=message_lengths_recent,
                response_times_recent=response_times_recent,
                emoji_count_recent=emoji_count_recent,
                topic_switches_recent=topic_switches_recent,
                self_disclosures_recent=self_disclosures_recent,
            )

            # ── 5. Feeling Detection (multi-dim) ──────────────────
            feeling = feeling_detector.detect(
                message_text,
                message_history=recent_user_msgs,
                behavioral_signals=computed_signals,
            )


            # Store feeling snapshot
            feeling_snapshot = FeelingSnapshot(
                user_id=user.id,
                valence=feeling.get("valence", 0.0),
                arousal=feeling.get("arousal", 0.0),
                dominance=feeling.get("dominance", 0.0),
                social_warmth=feeling.get("social_warmth", 0.0),
                vulnerability=feeling.get("vulnerability", 0.0),
                need=feeling.get("need", ""),
                subtext=feeling.get("subtext", ""),
                micro_emotion=feeling.get("micro_emotion", ""),
                confidence=feeling.get("confidence", 0.0),
            )
            session.add(feeling_snapshot)

            # ── 6. Need Analysis ──────────────────────────────────
            need_result = need_analyzer.analyze(feeling, message_text)

            # ── 7. Defense Detection ──────────────────────────────
            context_history = [{"feeling": feeling}]
            defense_result = defense_detector.detect(
                message_text,
                context_history=context_history,
            )

            # ── 7.5 Distress Detection & CARE Protocol ───────────
            # Track recent valences for sudden-change detection
            recent_valences = prev_state.get("recent_valences", [])
            recent_valences.append(feeling.get("valence", 0.0))
            if len(recent_valences) > 20:
                recent_valences = recent_valences[-20:]

            distress_result = detect_distress(
                message_text,
                feeling_valence=feeling.get("valence"),
                hour=prev_state.get("last_signals", {}).get("hour_of_day"),
            )
            care_instructions = distress_result.get("care_instructions", "")
            if distress_result.get("care_active"):
                logger.info("CARE protocol activated for user_id=%d (score=%.2f)", user.id, distress_result["total_score"])

            # ── 8. Response Mode Selection (8 modes) ──────────────
            rel_level = relationship_engine.get_level(user.relationship_score)
            selected_mode = response_selector.select(
                feeling=feeling,
                need_result=need_result,
                relationship_level=rel_level,
                interaction_count=user.relationship_score,
            )
            mode_id = selected_mode.get("id", "comfort")
            mode_instructions = response_selector.get_instructions(mode_id)
            mode_temperature = response_selector.get_temperature(mode_id)

            # ── 9. Model Router (auto-select provider) ────────────
            router_result = model_router.select(
                response_mode=mode_id,
                available_providers=list(ai_client.providers.keys()) if hasattr(ai_client, "providers") else None,
                active_provider=ai_client.get_active_provider() if hasattr(ai_client, "get_active_provider") else "groq",
            )
            router_provider = router_result.get("provider", ai_client.get_active_provider() if hasattr(ai_client, "get_active_provider") else "groq")

            # ── 10. Retrieve memories ─────────────────────────────
            memories_summary = await get_memories_summary(session, user.id)

            # ── 11. Retrieve preferences ──────────────────────────
            prefs = await get_user_preferences(session, user.id)
            preferences_text = _format_preferences(prefs)

            # ── 12. Determine personality ─────────────────────────
            personality = personality_engine.get_personality(user.current_personality)
            personality_instructions = personality_engine.get_instructions(user.current_personality)

            # ── 13. Determine mood ────────────────────────────────
            mood = mood_engine.determine_mood(
                current_mood=user.current_mood,
                relationship_score=user.relationship_score,
            )
            mood_instructions = mood_engine.get_instructions(mood)

            # ── 14. Relationship instructions ─────────────────────
            rel_instructions = relationship_engine.get_instructions(user.relationship_score)

            # ── 15. Build system prompt with mode instructions ────
            # Merge mode instructions into the system prompt
            enhanced_mood = f"{mood_instructions}\n\nResponse Mode: {selected_mode.get('name', 'Comfort')}\n{mode_instructions}"
            if care_instructions:
                enhanced_mood += f"\n\nCARE PROTOCOL ACTIVE:\n{care_instructions}"
            if defense_result.get("primary", "none") != "none":
                enhanced_mood += f"\n\nDefense strategy: {defense_result.get('strategy', '')}"

            scaffold_instructions = get_scaffold_instructions(rel_level)

            system_prompt = prompt_builder.build_system_prompt(
                personality_name=user.current_personality.capitalize(),
                personality=personality,
                mood_name=mood.name,
                mood=mood,
                relationship_level=rel_level,
                relationship_instructions=rel_instructions,
                user_name=user.display_name or user_tg.first_name or "User",
                language=user.language,
                preferences=preferences_text,
                memories=memories_summary,
                personality_instructions=personality_instructions,
                mood_instructions=enhanced_mood,
                scaffold_instructions=scaffold_instructions,
            )

            # ── 16. Build messages & call AI ─────────────────────
            messages = prompt_builder.build_messages(
                system_prompt,
                conversation_context,
                message_text,
            )

            # Set provider temperature based on selected mode
            orig_active = None
            if hasattr(ai_client, "get_active_provider") and router_provider:
                orig_active = ai_client.get_active_provider()
                if router_provider != orig_active:
                    try:
                        ai_client.set_active_provider(router_provider)
                    except Exception:
                        logger.warning("Could not switch to provider %s", router_provider)

            ai_response = await ai_client.chat_completion(
                messages,
                temperature=mode_temperature,
            )

            # Restore original provider if needed
            if orig_active and hasattr(ai_client, "set_active_provider"):
                try:
                    ai_client.set_active_provider(orig_active)
                except Exception:
                    pass

            # ── 17. Clean response ────────────────────────────────
            cleaned = clean_response(ai_response)

            # ── 18. Save AI response ──────────────────────────────
            await save_message(session, user.id, "assistant", cleaned)

            # ── 19. Encode as training sample ─────────────────────
            relationship_state = {
                "level": rel_level,
                "score": user.relationship_score,
                "trust": 0.0,  # Will be updated by relationship dimensions
            }
            sample, embedding = conversation_encoder.encode_and_embed(
                user_message=message_text,
                conversation_context=conversation_context or "",
                ai_response=cleaned,
                response_mode=mode_id,
                user_memories=memories_summary or "",
                relationship_state=relationship_state,
                detected_feeling=feeling,
                quality_score=0.0,  # Will be updated on next message
            )

            training_record = TrainingSample(
                user_id=user.id,
                interaction_json=json.dumps(sample),
                quality_score=0.0,
            )
            session.add(training_record)
            await session.commit()
            await session.refresh(training_record)

            # Store state for deferred quality scoring
            if len(_user_message_history) > 1000:
                oldest_keys = list(_user_message_history.keys())[:100]
                for k in oldest_keys:
                    _user_message_history.pop(k, None)

            _user_message_history[user.id] = {
                "last_assistant_msg": cleaned,

                "last_sample_id": training_record.id,
                "prev_msg": message_text,
                "last_response_time": None,
                "last_signals": {
                    "hour_of_day": datetime.now(timezone.utc).hour,
                    "message_length": len(message_text),
                },
                "last_mode": mode_id,
                "recent_valences": recent_valences,
            }

            # ── 20. Update relationship score + dimensions ────────
            increase = relationship_engine.calculate_score_increase(
                len(message_text),
                user.relationship_score,
            )
            user.relationship_score += increase
            user.current_mood = mood.name

            # Update multi-dim relationship
            await _update_relationship_dimensions(
                session, user.id, feeling, increase
            )

            await session.commit()

            # ── 21. Send reply ────────────────────────────────────
            await _send_reply(update, cleaned)

        except Exception:
            logger.exception("Error processing message from %s.", user_tg.id)
            await update.message.reply_text(
                "Oops... I couldn't think of a reply just now. "
                "Could you try again in a moment? 🌸",
            )


# ── Internal helpers ─────────────────────────────────────────────────────


async def _send_reply(update: Update, text: str) -> None:
    """Send a reply, splitting into multiple messages if needed.

    Falls back to plain text if Markdown parsing fails.
    """
    chunks = split_long_message(text)
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode="Markdown")
        except telegram.error.BadRequest:
            try:
                await update.message.reply_text(chunk)
            except Exception as exc:
                logger.warning("Failed to send reply: %s", exc)


async def _update_relationship_dimensions(
    session: AsyncSession,
    user_id: int,
    feeling: dict[str, Any],
    score_increase: int,
) -> None:
    """Update multi-dimensional relationship state based on interaction."""
    from sqlalchemy import select

    stmt = select(RelationshipDimension).where(RelationshipDimension.user_id == user_id)
    result = await session.execute(stmt)
    dim = result.scalar_one_or_none()

    if dim is None:
        dim = RelationshipDimension(user_id=user_id)
        session.add(dim)

    # Calculate dimension changes based on feeling
    valence = feeling.get("valence", 0.0)
    vulnerability = feeling.get("vulnerability", 0.0)
    social_warmth = feeling.get("social_warmth", 0.5)

    # Trust grows when user is vulnerable and handled well
    if vulnerability > 0.5 and valence > -0.2:
        dim.trust = min(1.0, dim.trust + 0.02)
    elif valence < -0.5 and vulnerability < 0.2:
        dim.trust = max(0.0, dim.trust - 0.01)

    # Intimacy grows with vulnerability and positive valence
    if vulnerability > 0.6:
        dim.intimacy = min(1.0, dim.intimacy + 0.03)
    if valence > 0.4:
        dim.intimacy = min(1.0, dim.intimacy + 0.01)

    # Comfort grows with positive interactions
    if valence > 0.2 and social_warmth > 0.5:
        dim.comfort = min(1.0, dim.comfort + 0.02)

    # Attraction grows with affectionate interactions
    need = feeling.get("need", "")
    if need == "connection" and valence > 0:
        dim.attraction = min(1.0, dim.attraction + 0.01)

    # Respect grows consistently
    if score_increase > 0:
        dim.respect = min(1.0, dim.respect + 0.005)

    # Dependency grows with connection need (tracked to avoid anxious attachment)
    if need == "connection" and vulnerability > 0.4:
        dim.dependency = min(0.8, dim.dependency + 0.01)
    else:
        dim.dependency = max(0.0, dim.dependency - 0.002)


def _format_preferences(prefs) -> str:
    """Format a user's preferences object into a readable string."""
    if prefs is None:
        return "No custom preferences."

    lines: list[str] = []
    mapping = {
        "emoji_level": "Emoji level",
        "reply_length": "Reply length",
        "default_personality": "Default personality",
        "language": "Language",
        "memory_enabled": "Memory enabled",
    }
    for attr, label in mapping.items():
        value = getattr(prefs, attr, None)
        if value is not None:
            lines.append(f"- {label}: {value}")

    return "\n".join(lines) if lines else "No custom preferences."

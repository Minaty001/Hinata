"""
Hinata Core Brain — Shared Orchestration Layer

Coordinates feeling detection, need analysis, defense detection, mood shifts,
personality, memories summary, model routing, and response selection in a
unified pipeline for all clients (Web, Android, Telegram).
"""
from __future__ import annotations

import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Inject path references to support imports from both legacy and backend runtimes
ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Backend imports
from app.database.models import (
    User,
    Chain,
    Conversation,
    Memory,
    FeelingSnapshot,
    TrainingSample,
    RelationshipDimension,
)

# AI Engines (from root codebase)
from ai.feeling_detector import FeelingDetector
from ai.need_analyzer import NeedAnalyzer
from ai.defense_detector import DefenseDetector
from ai.response_mode_selector import ResponseModeSelector
from ai.personality_engine import PersonalityEngine
from ai.mood_engine import MoodEngine
from ai.relationship_engine import RelationshipEngine
from ai.prompt_builder import PromptBuilder
from ai.unified_ai_client import UnifiedAIClient
from ai.vulnerability_scaffold import get_scaffold_instructions
from ai.distress_detector import detect_distress
from ai.response_cleaner import clean_response, split_long_message
from ai.context_builder import build_conversation_context

from memory.memory_manager import get_memories_summary
from services.chat_service import save_message, get_conversation_history, get_or_create_chain, auto_index_session
from services.user_service import get_user_preferences

from training.behavioral_tracker import BehavioralTracker
from training.quality_scorer import QualityScorer
from training.conversation_encoder import ConversationEncoder
from training.model_router import ModelRouter

logger = logging.getLogger(__name__)


class BrainResult:
    """Standardized response from the Hinata Core Brain."""

    def __init__(
        self,
        reply: str,
        chain_id: str,
        provider: str,
        model: str,
        timestamp: datetime,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self.reply = reply
        self.chain_id = chain_id
        self.provider = provider
        self.model = model
        self.timestamp = timestamp
        self.metadata = metadata or {}


class HinataBrain:
    """Central Brain class orchestrating conversational state and AI execution."""

    def __init__(self) -> None:
        self.feeling_detector = FeelingDetector()
        self.need_analyzer = NeedAnalyzer()
        self.defense_detector = DefenseDetector()
        self.response_selector = ResponseModeSelector()
        self.personality_engine = PersonalityEngine()
        self.mood_engine = MoodEngine()
        self.relationship_engine = RelationshipEngine()
        self.prompt_builder = PromptBuilder()
        self.unified_client = UnifiedAIClient()
        self.behavioral_tracker = BehavioralTracker()
        self.quality_scorer = QualityScorer()
        self.conversation_encoder = ConversationEncoder()
        self.model_router = ModelRouter()

        # Shared user memory for deferred quality score tracking
        self._user_message_history: dict[int, dict[str, Any]] = {}

    async def handle(
        self,
        *,
        user: User,
        message: str,
        source: str,  # "web" | "android" | "telegram"
        chain_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        session: AsyncSession,
    ) -> BrainResult:
        """Process an incoming message through the unified AI companion pipeline."""
        message_text = message.strip()
        if not message_text:
            raise ValueError("Message cannot be empty")

        # 1. Ensure active chain/thread exists
        active_chain = await get_or_create_chain(session, user.id, chain_id=chain_id)
        actual_chain_id = active_chain.chain_id

        # 2. Deferred quality scoring for the previous interaction loop
        prev_state = self._user_message_history.get(user.id, {})
        last_assistant_msg = prev_state.get("last_assistant_msg", "")
        if last_assistant_msg:
            score_result = self.quality_scorer.score_interaction(
                user_replied=True,
                user_replied_quickly=(prev_state.get("last_response_time") or 999) < 120,
                user_expanded_topic=(len(message_text) > len(prev_state.get("prev_msg", "")) + 20),
                user_showed_affection=any(
                    w in message_text.lower()
                    for w in ["love", "thank", "❤️", "💕", "sweet", "amazing"]
                ),
                user_opened_up_more=len(message_text) > 200,
                message_length=len(message_text),
            )
            # Update the quality score of the previous training sample record
            prev_sample_id = prev_state.get("last_sample_id")
            if prev_sample_id:
                try:
                    stmt = select(TrainingSample).where(TrainingSample.id == prev_sample_id)
                    result = await session.execute(stmt)
                    sample = result.scalar_one_or_none()
                    if sample:
                        sample.quality_score = score_result["score"]
                        await session.commit()
                except Exception as exc:
                    logger.warning("Could not update quality score for sample %s: %s", prev_sample_id, exc)

        # 3. Retrieve conversation history & build context
        conversation_context = await build_conversation_context(session, user.id, chain_id=actual_chain_id)
        recent_msgs = await get_conversation_history(session, user.id, limit=10)
        recent_user_msgs = [m.message for m in recent_msgs if m.role == "user"]

        # 4. Save current user message turn to Database
        await save_message(session, user.id, "user", message_text, chain_id=actual_chain_id)

        # 5. Compute dynamic behavioral signals
        user_msgs = [m for m in recent_msgs if m.role == "user"]
        message_lengths_recent = [len(m.message) for m in user_msgs]
        
        response_times_recent = []
        for i in range(1, len(recent_msgs)):
            if recent_msgs[i].role == "user" and recent_msgs[i - 1].role == "assistant":
                dt = (recent_msgs[i].timestamp - recent_msgs[i - 1].timestamp).total_seconds()
                response_times_recent.append(dt)

        emoji_pattern = re.compile(r"[\u263a-\u263f\u2700-\u27bf\U0001f300-\U0001f9ff]")
        emoji_count_recent = [len(emoji_pattern.findall(m.message)) for m in user_msgs]
        topic_switches_recent = [len(m.message) < 50 for m in user_msgs]
        self_disclosures_recent = [
            any(w in m.message.lower() for w in ["i feel", "my", "i am", "me", "personally"])
            for m in user_msgs
        ]

        current_time = time.time()
        last_response_time = None
        if recent_msgs and recent_msgs[-1].role == "assistant" and recent_msgs[-1].timestamp:
            ts = recent_msgs[-1].timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            last_response_time = (datetime.now(timezone.utc) - ts).total_seconds()

        computed_signals = self.behavioral_tracker.compute_signals(
            current_time=current_time,
            last_response_time=last_response_time,
            message_length=len(message_text),
            message_lengths_recent=message_lengths_recent,
            response_times_recent=response_times_recent,
            emoji_count_recent=emoji_count_recent,
            topic_switches_recent=topic_switches_recent,
            self_disclosures_recent=self_disclosures_recent,
        )

        # 6. Emotion/Feeling Detection
        feeling = self.feeling_detector.detect(
            message_text,
            message_history=recent_user_msgs,
            behavioral_signals=computed_signals,
        )

        # Save feeling snapshot
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

        # 7. Needs and Psychological Defense analysis
        need_result = self.need_analyzer.analyze(feeling, message_text)
        context_history = [{"feeling": feeling}]
        defense_result = self.defense_detector.detect(
            message_text,
            context_history=context_history,
        )

        # 8. Distress Detection & CARE Protocol
        recent_valences = prev_state.get("recent_valences", [])
        recent_valences.append(feeling.get("valence", 0.0))
        if len(recent_valences) > 20:
            recent_valences = recent_valences[-20:]

        distress_result = detect_distress(
            message_text,
            feeling_valence=feeling.get("valence"),
            hour=datetime.now(timezone.utc).hour,
        )
        care_instructions = distress_result.get("care_instructions", "")

        # 9. Response Mode Selection
        rel_level = self.relationship_engine.get_level(user.relationship_score)
        selected_mode = self.response_selector.select(
            feeling=feeling,
            need_result=need_result,
            relationship_level=rel_level,
            interaction_count=user.relationship_score,
        )
        mode_id = selected_mode.get("id", "comfort")
        mode_instructions = self.response_selector.get_instructions(mode_id)
        mode_temperature = self.response_selector.get_temperature(mode_id)

        # 10. Model Routing & AI Client Configuration
        active_prov = provider or self.unified_client.get_active_provider()
        router_result = self.model_router.select(
            response_mode=mode_id,
            available_providers=list(self.unified_client.providers.keys()),
            active_provider=active_prov,
        )
        router_provider = router_result.get("provider", active_prov)

        # 11. Retrieve Memories & User Preferences
        memories_summary = await get_memories_summary(session, user.id)
        prefs = await get_user_preferences(session, user.id)
        preferences_text = self._format_preferences(prefs)

        # 12. Personality & Mood State resolution
        personality = self.personality_engine.get_personality(user.current_personality)
        personality_instructions = self.personality_engine.get_instructions(user.current_personality)
        mood = self.mood_engine.determine_mood(
            current_mood=user.current_mood,
            relationship_score=user.relationship_score,
        )
        mood_instructions = self.mood_engine.get_instructions(mood)

        # 13. Relationship Level Instructions
        rel_instructions = self.relationship_engine.get_instructions(user.relationship_score)

        # 14. Build prompt structures
        enhanced_mood = f"{mood_instructions}\n\nResponse Mode: {selected_mode.get('name', 'Comfort')}\n{mode_instructions}"
        if care_instructions:
            enhanced_mood += f"\n\nCARE PROTOCOL ACTIVE:\n{care_instructions}"
        if defense_result.get("primary", "none") != "none":
            enhanced_mood += f"\n\nDefense strategy: {defense_result.get('strategy', '')}"

        scaffold_instructions = get_scaffold_instructions(rel_level)

        system_prompt = self.prompt_builder.build_system_prompt(
            personality_name=user.current_personality.capitalize(),
            personality=personality,
            mood_name=mood.name,
            mood=mood,
            relationship_level=rel_level,
            relationship_instructions=rel_instructions,
            user_name=user.display_name or "User",
            language=user.language,
            preferences=preferences_text,
            memories=memories_summary,
            personality_instructions=personality_instructions,
            mood_instructions=enhanced_mood,
            scaffold_instructions=scaffold_instructions,
        )

        messages_payload = self.prompt_builder.build_messages(
            system_prompt,
            conversation_context,
            message_text,
        )

        # 15. Call Unified AI Client using routed provider
        orig_active = self.unified_client.get_active_provider()
        if router_provider != orig_active:
            try:
                self.unified_client.set_active_provider(router_provider, model)
            except Exception as exc:
                logger.warning("Could not switch to routed provider %s: %s", router_provider, exc)

        try:
            ai_response = await self.unified_client.chat_completion(
                messages_payload,
                model=model,
                temperature=mode_temperature,
            )
        finally:
            # Restore original provider configuration
            if orig_active != self.unified_client.get_active_provider():
                try:
                    self.unified_client.set_active_provider(orig_active)
                except Exception:
                    pass

        # 16. Clean response
        cleaned_reply = clean_response(ai_response)

        # 17. Save Assistant Message Turn to Database
        await save_message(session, user.id, "assistant", cleaned_reply, chain_id=actual_chain_id)

        # 18. Encode as Training Sample & Save to DB
        relationship_state = {
            "level": rel_level,
            "score": user.relationship_score,
            "trust": 0.0,
        }
        sample, _ = self.conversation_encoder.encode_and_embed(
            user_message=message_text,
            conversation_context=conversation_context or "",
            ai_response=cleaned_reply,
            response_mode=mode_id,
            user_memories=memories_summary or "",
            relationship_state=relationship_state,
            detected_feeling=feeling,
            quality_score=0.0,
        )

        training_record = TrainingSample(
            user_id=user.id,
            interaction_json=json.dumps(sample),
            quality_score=0.0,
        )
        session.add(training_record)
        await session.commit()
        await session.refresh(training_record)

        # Save deferred quality tracking state
        self._user_message_history[user.id] = {
            "last_assistant_msg": cleaned_reply,
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

        # 19. Update Relationship Score & Dimensions
        score_increase = self.relationship_engine.calculate_score_increase(
            len(message_text),
            user.relationship_score,
        )
        user.relationship_score += score_increase
        user.current_mood = mood.name

        await self._update_relationship_dimensions(session, user.id, feeling, score_increase)

        # 20. Auto-index session topics asynchronously for fast proceed lookup
        await auto_index_session(session, user.id, actual_chain_id)

        await session.commit()

        # 21. Build structured result containing metadata
        active_p = self.unified_client.get_active_provider()
        active_m = self.unified_client.providers.get(active_p, {}).get("active_model", "default")

        return BrainResult(
            reply=cleaned_reply,
            chain_id=actual_chain_id,
            provider=active_p,
            model=active_m,
            timestamp=datetime.now(timezone.utc),
            metadata={
                "feeling": feeling,
                "need": need_result,
                "defense": defense_result,
                "mode": mode_id,
                "score_increase": score_increase,
            },
        )

    async def _update_relationship_dimensions(
        self,
        session: AsyncSession,
        user_id: int,
        feeling: dict[str, Any],
        score_increase: int,
    ) -> None:
        """Update multi-dimensional relationship metrics."""
        stmt = select(RelationshipDimension).where(RelationshipDimension.user_id == user_id)
        result = await session.execute(stmt)
        dim = result.scalar_one_or_none()

        if dim is None:
            dim = RelationshipDimension(user_id=user_id)
            session.add(dim)

        valence = feeling.get("valence", 0.0)
        vulnerability = feeling.get("vulnerability", 0.0)
        social_warmth = feeling.get("social_warmth", 0.5)

        # Get current dimension values, fallback to schema defaults if None
        trust = dim.trust if dim.trust is not None else 0.1
        intimacy = dim.intimacy if dim.intimacy is not None else 0.0
        comfort = dim.comfort if dim.comfort is not None else 0.1
        attraction = dim.attraction if dim.attraction is not None else 0.0
        respect = dim.respect if dim.respect is not None else 0.1
        dependency = dim.dependency if dim.dependency is not None else 0.0

        # Trust
        if vulnerability > 0.5 and valence > -0.2:
            dim.trust = min(1.0, trust + 0.02)
        elif valence < -0.5 and vulnerability < 0.2:
            dim.trust = max(0.0, trust - 0.01)
        else:
            dim.trust = trust

        # Intimacy
        if vulnerability > 0.6:
            intimacy = min(1.0, intimacy + 0.03)
        if valence > 0.4:
            intimacy = min(1.0, intimacy + 0.01)
        dim.intimacy = intimacy

        # Comfort
        if valence > 0.2 and social_warmth > 0.5:
            dim.comfort = min(1.0, comfort + 0.02)
        else:
            dim.comfort = comfort

        # Attraction
        need = feeling.get("need", "")
        if need == "connection" and valence > 0:
            dim.attraction = min(1.0, attraction + 0.01)
        else:
            dim.attraction = attraction

        # Respect
        if score_increase > 0:
            dim.respect = min(1.0, respect + 0.005)
        else:
            dim.respect = respect

        # Dependency
        if need == "connection" and vulnerability > 0.4:
            dim.dependency = min(0.8, dependency + 0.01)
        else:
            dim.dependency = max(0.0, dependency - 0.002)

    def _format_preferences(self, prefs: Any) -> str:
        """Format preferences model into a readable system prompt string."""
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


# Export global core brain instance
brain = HinataBrain()

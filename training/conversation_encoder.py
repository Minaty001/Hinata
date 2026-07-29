"""
Hinata - Conversation Encoder

Every interaction is immediately encoded as a structured training sample
with full context: user message, detected feeling, response mode, and
engagement metrics.

These samples feed into the continuous learning pipeline.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from training.feature_embedder import FeatureEmbedder

logger = logging.getLogger(__name__)


class ConversationEncoder:
    """Encodes every user↔AI interaction into a structured training sample."""

    def __init__(self, embedder: FeatureEmbedder | None = None) -> None:
        self.embedder = embedder or FeatureEmbedder()

    def encode_interaction(
        self,
        *,
        user_message: str,
        conversation_context: str,
        ai_response: str,
        response_mode: str,
        user_memories: str = "",
        relationship_state: dict[str, Any] | None = None,
        detected_feeling: dict[str, Any] | None = None,
        quality_score: float = 0.0,
    ) -> dict[str, Any]:
        """Encode a single interaction as a structured training sample.

        Args:
            user_message: The user's message text.
            conversation_context: Recent conversation history.
            ai_response: Hinata's response text.
            response_mode: Which response mode was used.
            user_memories: Memory summary string.
            relationship_state: Multi-dim relationship state dict.
            detected_feeling: Feeling snapshot dict.
            quality_score: Pre-computed quality score (0.0 if unknown yet).

        Returns:
            A training sample dict ready for storage.
        """
        sample: dict[str, Any] = {
            "interaction_id": f"int-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input": {
                "user_message": user_message,
                "conversation_context": conversation_context[:2000],
                "user_memories": user_memories[:500],
                "relationship_state": relationship_state or {},
                "detected_feeling": detected_feeling or {},
            },
            "output": {
                "response_mode": response_mode,
                "response_text": ai_response[:2000],
                "relationship_impact": self._compute_impact(detected_feeling),
            },
            "metrics": {
                "user_satisfaction_proxy": 0.0,
                "conversation_continuation": True,
            },
            "quality_score": quality_score,
        }
        return sample

    def encode_and_embed(
        self,
        *,
        user_message: str,
        conversation_context: str,
        ai_response: str,
        response_mode: str,
        user_memories: str = "",
        relationship_state: dict[str, Any] | None = None,
        detected_feeling: dict[str, Any] | None = None,
        quality_score: float = 0.0,
    ) -> tuple[dict[str, Any], list[float]]:
        """Encode interaction and also produce an embedding vector.

        Returns:
            Tuple of (training_sample_dict, embedding_vector).
        """
        sample = self.encode_interaction(
            user_message=user_message,
            conversation_context=conversation_context,
            ai_response=ai_response,
            response_mode=response_mode,
            user_memories=user_memories,
            relationship_state=relationship_state,
            detected_feeling=detected_feeling,
            quality_score=quality_score,
        )

        # Create embedding from combined text features
        combined = f"{user_message} {ai_response} {response_mode}"
        embedding = self.embedder.embed_text(combined)
        sample["embedding"] = embedding

        return sample, embedding

    # ── Internal ───────────────────────────────────────────────────

    @staticmethod
    def _compute_impact(
        detected_feeling: dict[str, Any] | None,
    ) -> dict[str, float]:
        """Estimate relationship impact based on detected feeling."""
        if not detected_feeling:
            return {"trust": 0.0, "intimacy": 0.0, "comfort": 0.0}

        impact: dict[str, float] = {"trust": 0.0, "intimacy": 0.0, "comfort": 0.0}

        # Positive valence → growing trust & comfort
        valence = detected_feeling.get("valence", 0.0)
        if valence > 0.3:
            impact["trust"] = 0.02
            impact["comfort"] = 0.03
        elif valence < -0.3:
            impact["trust"] = -0.01

        # Vulnerability → intimacy grows
        vulnerability = detected_feeling.get("vulnerability", 0.0)
        if vulnerability > 0.6:
            impact["intimacy"] = 0.03
            impact["trust"] = 0.02

        # Need-based adjustments
        need = detected_feeling.get("need", "")
        if need == "connection":
            impact["intimacy"] += 0.02
        elif need == "autonomy":
            impact["trust"] += 0.01


        return impact

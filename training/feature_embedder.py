"""
Hinata - Feature Embedder

Converts text and behavioural data into vector embeddings for
AI-native memory and similarity search.

Uses a lightweight hash-based embedding approach by default so no
external model is required. When sentence-transformers is available,
it can be enabled for higher-quality semantic embeddings.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Default embedding dimension (matching common sentence-transformer models)
_DEFAULT_DIM = 384


class FeatureEmbedder:
    """Text-to-vector embedding with configurable dimension."""

    def __init__(self, dimension: int = _DEFAULT_DIM) -> None:
        self.dimension = dimension
        self._use_sentence_transformer = False
        self._model = None
        self._try_load_sentence_transformer()

    def embed_text(self, text: str) -> list[float]:
        """Convert text to a dense vector embedding.

        Uses sentence-transformers if available; falls back to a
        deterministic hash-based embedding.

        Args:
            text: Input text to embed.

        Returns:
            A list of floats of length ``dimension``.
        """
        if not text:
            return [0.0] * self.dimension

        if self._use_sentence_transformer and self._model is not None:
            try:
                vec = self._model.encode(text, normalize_embeddings=True)
                return vec.tolist()
            except Exception as exc:
                logger.warning("sentence-transformers failed: %s, falling back", exc)

        return self._hash_embed(text)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts at once."""
        return [self.embed_text(t) for t in texts]

    def embed_behavioural(
        self,
        features: list[float],
    ) -> list[float]:
        """Pack behavioural features into a fixed-dimension vector.

        Args:
            features: Raw behavioural feature list (variable length).

        Returns:
            A fixed-dimension vector (padded or truncated).
        """
        arr = np.array(features, dtype=np.float32)
        if len(arr) < self.dimension:
            arr = np.pad(arr, (0, self.dimension - len(arr)))
        else:
            arr = arr[:self.dimension]
        return arr.tolist()

    def cosine_similarity(
        self, vec_a: list[float], vec_b: list[float]
    ) -> float:
        """Compute cosine similarity between two vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-10 or norm_b < 1e-10:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    # ── Internal ───────────────────────────────────────────────────

    def _hash_embed(self, text: str) -> list[float]:
        """Deterministic hash-based embedding (no external model needed)."""
        vec = np.zeros(self.dimension, dtype=np.float32)
        words = text.lower().split()
        for word in words:
            digest = hashlib.sha256(word.encode()).digest()
            # Map hash bytes to multiple positions with weights
            for i in range(min(4, len(digest) // 4)):
                idx = int.from_bytes(digest[i * 4:(i + 1) * 4], "little") % self.dimension
                vec[idx] += 1.0
        # Normalise
        norm = np.linalg.norm(vec)
        if norm > 1e-10:
            vec /= norm
        return vec.tolist()

    def _try_load_sentence_transformer(self) -> None:
        """Attempt to load sentence-transformers model (optional)."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
            self._use_sentence_transformer = True
            logger.info("Loaded sentence-transformer model (dim=%d).", self.dimension)
        except ImportError:
            logger.info("sentence-transformers not available; using hash embeddings.")
        except Exception as exc:
            logger.warning("Failed to load sentence-transformer: %s", exc)

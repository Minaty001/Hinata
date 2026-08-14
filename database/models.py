"""
Hinata - SQLAlchemy ORM Models

Defines all database tables used by Hinata.
Uses SQLAlchemy 2.0 declarative mapping with async support.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class User(Base):
    """Represents a Telegram user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    language: Mapped[str] = mapped_column(String(16), default="hinglish")
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")
    relationship_score: Mapped[int] = mapped_column(Integer, default=0)
    current_mood: Mapped[str] = mapped_column(String(32), default="happy")
    current_personality: Mapped[str] = mapped_column(String(32), default="sweet")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    first_interaction: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    last_interaction: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    chains = relationship("Chain", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("Preference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    identities = relationship("Identity", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


class Chain(Base):
    """Represents a conversation chain / thread session."""

    __tablename__ = "chains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chain_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), default="New Conversation")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="chains")
    conversations = relationship("Conversation", back_populates="chain", cascade="all, delete-orphan")
    indices = relationship("SessionIndex", back_populates="chain", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Chain(id={self.id}, chain_id={self.chain_id}, title={self.title})>"


class SessionIndex(Base):
    """Session Topic Index for fast query jump without loading full conversation logs."""

    __tablename__ = "session_indices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chain_id: Mapped[str] = mapped_column(String(64), ForeignKey("chains.chain_id", ondelete="CASCADE"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    chain = relationship("Chain", back_populates="indices")

    def __repr__(self) -> str:
        return f"<SessionIndex(id={self.id}, chain_id={self.chain_id}, topic={self.topic})>"


class Conversation(Base):
    """Stores individual message exchanges."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    chain_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("chains.chain_id", ondelete="CASCADE"), nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" or "assistant"
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    chain = relationship("Chain", back_populates="conversations")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, chain_id={self.chain_id}, role={self.role})>"


class Memory(Base):
    """Long-term memory entries for each user."""

    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # fact, preference, goal, event, etc.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=1)  # 1-5 scale
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="memories")

    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, type={self.type}, user_id={self.user_id})>"


class Preference(Base):
    """User preferences and settings."""

    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    emoji_level: Mapped[str] = mapped_column(String(16), default="normal")  # none, low, normal, high
    reply_length: Mapped[str] = mapped_column(String(16), default="normal")  # short, normal, long
    default_personality: Mapped[str] = mapped_column(String(32), default="sweet")
    language: Mapped[str] = mapped_column(String(16), default="hinglish")
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="preferences")

    def __repr__(self) -> str:
        return f"<Preference(id={self.id}, user_id={self.user_id})>"


class Setting(Base):
    """Global bot settings."""

    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:
        return f"<Setting(key={self.key}, value={self.value})>"


# ── Next-Level Plan: New Tables ─────────────────────────────────────────────


class FeelingSnapshot(Base):
    """Multi-dimensional emotion vector snapshot per user message."""

    __tablename__ = "feeling_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("conversations.id"), nullable=True)
    valence: Mapped[float] = mapped_column(Float, default=0.0)        # -1 to 1
    arousal: Mapped[float] = mapped_column(Float, default=0.0)        # 0 to 1
    dominance: Mapped[float] = mapped_column(Float, default=0.0)      # 0 to 1
    social_warmth: Mapped[float] = mapped_column(Float, default=0.0)  # 0 to 1
    vulnerability: Mapped[float] = mapped_column(Float, default=0.0)  # 0 to 1
    need: Mapped[str] = mapped_column(String(64), default="")
    subtext: Mapped[str] = mapped_column(Text, default="")
    micro_emotion: Mapped[str] = mapped_column(String(64), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)

    def __repr__(self) -> str:
        return f"<FeelingSnapshot(id={self.id}, user_id={self.user_id}, need={self.need})>"


class TrainingSample(Base):
    """Every interaction encoded as a structured training sample."""

    __tablename__ = "training_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    interaction_json: Mapped[str] = mapped_column(Text, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    def __repr__(self) -> str:
        return f"<TrainingSample(id={self.id}, user_id={self.user_id}, score={self.quality_score})>"


class RelationshipDimension(Base):
    """Multi-dimensional relationship state per user."""

    __tablename__ = "relationship_dimensions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    trust: Mapped[float] = mapped_column(Float, default=0.1)
    intimacy: Mapped[float] = mapped_column(Float, default=0.0)
    attraction: Mapped[float] = mapped_column(Float, default=0.0)
    comfort: Mapped[float] = mapped_column(Float, default=0.1)
    respect: Mapped[float] = mapped_column(Float, default=0.1)
    dependency: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    def __repr__(self) -> str:
        return f"<RelationshipDimension(user_id={self.user_id}, trust={self.trust})>"


class Identity(Base):
    """Cross-platform identity mapping (e.g. Telegram id -> internal User).

    Mirrors the same table used by the backend runtime so the root web
    layer stays self-consistent with services/user_service.py.
    """

    __tablename__ = "identities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    platform_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="identities")

    def __repr__(self) -> str:
        return f"<Identity(id={self.id}, user_id={self.user_id}, platform={self.platform})>"




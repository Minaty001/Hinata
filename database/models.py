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
    language: Mapped[str] = mapped_column(String(16), default="en")
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
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("Preference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


class Conversation(Base):
    """Stores individual message exchanges."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" or "assistant"
    message: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="conversations")

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, role={self.role}, user_id={self.user_id})>"


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
    language: Mapped[str] = mapped_column(String(16), default="en")
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

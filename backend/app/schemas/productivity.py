"""
Pydantic Schemas for Personal Productivity models (Tasks, Events, Goals)
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Tasks Schemas ──────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: str = "pending"
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None


class TaskSchema(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    status: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Events Schemas ─────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    recurrence: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    recurrence: Optional[str] = None


class EventSchema(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    location: Optional[str]
    recurrence: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Goals Schemas ──────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    target_description: Optional[str] = None
    current_value: float = 0.0
    target_value: float = 100.0
    unit: Optional[str] = "%"
    deadline: Optional[datetime] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    target_description: Optional[str] = None
    current_value: Optional[float] = None
    target_value: Optional[float] = None
    unit: Optional[str] = None
    deadline: Optional[datetime] = None


class GoalSchema(BaseModel):
    id: int
    user_id: int
    title: str
    target_description: Optional[str]
    current_value: float
    target_value: float
    unit: Optional[str]
    deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

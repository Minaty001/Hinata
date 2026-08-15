"""
FastAPI Router for Personal Productivity Services (/api/v1/productivity)

Provides CRUD interfaces for Tasks, Events, and Goals.
"""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Backend imports
from app.core.user import get_current_user
from app.database.engine import get_session
from app.database.models import User, Task, Event, Goal
from app.schemas.productivity import (
    TaskCreate, TaskUpdate, TaskSchema,
    EventCreate, EventUpdate, EventSchema,
    GoalCreate, GoalUpdate, GoalSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Tasks Router ───────────────────────────────────────────────────────────

@router.get("/tasks", response_model=list[TaskSchema])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve user's task list."""
    stmt = select(Task).where(Task.user_id == current_user.id).order_by(Task.created_at.desc())
    res = await session.execute(stmt)
    return res.scalars().all()


@router.post("/tasks", response_model=TaskSchema)
async def create_task(
    request: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new task."""
    task = Task(
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        status=request.status,
        due_date=request.due_date,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.put("/tasks/{task_id}", response_model=TaskSchema)
async def update_task(
    task_id: int,
    request: TaskUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update an existing task."""
    stmt = select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    res = await session.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for k, v in request.model_dump(exclude_unset=True).items():
        setattr(task, k, v)

    await session.commit()
    await session.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Deletes a user's task."""
    stmt = select(Task).where(Task.id == task_id, Task.user_id == current_user.id)
    res = await session.execute(stmt)
    task = res.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    await session.delete(task)
    await session.commit()
    return


# ── Events Router ──────────────────────────────────────────────────────────

@router.get("/events", response_model=list[EventSchema])
async def list_events(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve user's scheduled events."""
    stmt = select(Event).where(Event.user_id == current_user.id).order_by(Event.start_time.asc())
    res = await session.execute(stmt)
    return res.scalars().all()


@router.post("/events", response_model=EventSchema)
async def create_event(
    request: EventCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new scheduled event."""
    event = Event(
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        start_time=request.start_time,
        end_time=request.end_time,
        location=request.location,
        recurrence=request.recurrence,
    )
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


@router.put("/events/{event_id}", response_model=EventSchema)
async def update_event(
    event_id: int,
    request: EventUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update an existing event."""
    stmt = select(Event).where(Event.id == event_id, Event.user_id == current_user.id)
    res = await session.execute(stmt)
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    for k, v in request.model_dump(exclude_unset=True).items():
        setattr(event, k, v)

    await session.commit()
    await session.refresh(event)
    return event


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Deletes an event."""
    stmt = select(Event).where(Event.id == event_id, Event.user_id == current_user.id)
    res = await session.execute(stmt)
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    await session.delete(event)
    await session.commit()
    return


# ── Goals Router ───────────────────────────────────────────────────────────

@router.get("/goals", response_model=list[GoalSchema])
async def list_goals(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Retrieve user's active goals."""
    stmt = select(Goal).where(Goal.user_id == current_user.id).order_by(Goal.created_at.desc())
    res = await session.execute(stmt)
    return res.scalars().all()


@router.post("/goals", response_model=GoalSchema)
async def create_goal(
    request: GoalCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new goal."""
    goal = Goal(
        user_id=current_user.id,
        title=request.title,
        target_description=request.target_description,
        current_value=request.current_value,
        target_value=request.target_value,
        unit=request.unit,
        deadline=request.deadline,
    )
    session.add(goal)
    await session.commit()
    await session.refresh(goal)
    return goal


@router.put("/goals/{goal_id}", response_model=GoalSchema)
async def update_goal(
    goal_id: int,
    request: GoalUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Update progress or settings of an existing goal."""
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    res = await session.execute(stmt)
    goal = res.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    for k, v in request.model_dump(exclude_unset=True).items():
        setattr(goal, k, v)

    await session.commit()
    await session.refresh(goal)
    return goal


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Deletes a goal."""
    stmt = select(Goal).where(Goal.id == goal_id, Goal.user_id == current_user.id)
    res = await session.execute(stmt)
    goal = res.scalar_one_or_none()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    await session.delete(goal)
    await session.commit()
    return

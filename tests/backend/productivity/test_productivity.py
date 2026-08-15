"""
Tests for Hinata Productivity services (Tasks, Events, Goals).

Verifies CRUD REST endpoints and runtime system productivity tool execution.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Backend imports
from app.database.models import Task, Event, Goal, User
from app.runtime.registry import AddTaskTool, AddEventTool, AddGoalTool
from tests.backend.conftest import TestSessionMaker


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Yield an active test database session."""
    async with TestSessionMaker() as session:
        yield session


async def _current_user_id(client: AsyncClient) -> int:
    """Fetch the single local user's id from the database (no auth)."""
    from app.core.user import get_default_user
    async with TestSessionMaker() as session:
        user = await get_default_user(session)
        return user.id


@pytest.mark.asyncio
async def test_tasks_crud(client: AsyncClient):
    user_id = await _current_user_id(client)

    # 1. Create Task
    create_res = await client.post(
        "/api/v1/productivity/tasks",
        json={
            "title": "Buy milk",
            "description": "2% fat milk from supermarket",
            "due_date": "2026-12-31T23:59:59"
        }
    )
    assert create_res.status_code == 200
    task_id = create_res.json()["id"]

    # 2. List Tasks
    list_res = await client.get("/api/v1/productivity/tasks")
    assert list_res.status_code == 200
    tasks = list_res.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Buy milk"

    # 3. Update Task
    update_res = await client.put(
        f"/api/v1/productivity/tasks/{task_id}",
        json={"status": "completed"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "completed"

    # 4. Delete Task
    del_res = await client.delete(f"/api/v1/productivity/tasks/{task_id}")
    assert del_res.status_code == 204

    # 5. List empty
    list_empty = await client.get("/api/v1/productivity/tasks")
    assert len(list_empty.json()) == 0


@pytest.mark.asyncio
async def test_events_crud(client: AsyncClient):
    user_id = await _current_user_id(client)

    # 1. Create Event
    create_res = await client.post(
        "/api/v1/productivity/events",
        json={
            "title": "Doctor Appointment",
            "start_time": "2026-08-20T10:00:00",
            "location": "City Clinic"
        }
    )
    assert create_res.status_code == 200
    event_id = create_res.json()["id"]

    # 2. List Events
    list_res = await client.get("/api/v1/productivity/events")
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["location"] == "City Clinic"

    # 3. Delete Event
    del_res = await client.delete(f"/api/v1/productivity/events/{event_id}")
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_goals_crud(client: AsyncClient):
    user_id = await _current_user_id(client)

    # 1. Create Goal
    create_res = await client.post(
        "/api/v1/productivity/goals",
        json={
            "title": "Run 50km",
            "target_value": 50.0,
            "unit": "km"
        }
    )
    assert create_res.status_code == 200
    goal_id = create_res.json()["id"]

    # 2. List Goals
    list_res = await client.get("/api/v1/productivity/goals")
    assert len(list_res.json()) == 1
    assert list_res.json()[0]["target_value"] == 50.0

    # 3. Update Goal progress
    update_res = await client.put(
        f"/api/v1/productivity/goals/{goal_id}",
        json={"current_value": 15.5}
    )
    assert update_res.status_code == 200
    assert update_res.json()["current_value"] == 15.5

    # 4. Delete Goal
    del_res = await client.delete(f"/api/v1/productivity/goals/{goal_id}")
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_productivity_runtime_tools(client: AsyncClient, db_session: AsyncSession):
    # Setup mock companion user profile
    user_id = await _current_user_id(client)
    
    # 1. Run AddTaskTool execution
    from unittest.mock import patch
    with patch("app.database.engine.AsyncSessionMaker") as mock_maker:
        mock_context = MagicMock()
        mock_context.__aenter__.return_value = db_session
        mock_context.__aexit__ = AsyncMock()
        mock_maker.return_value = mock_context

        # Add Task Tool
        task_tool = AddTaskTool()
        res_task = await task_tool.execute(
            user_id=user_id,
            title="Read book",
            description="Read 2 chapters"
        )
        assert "created successfully" in res_task

        # Add Event Tool
        event_tool = AddEventTool()
        res_event = await event_tool.execute(
            user_id=user_id,
            title="Meeting with Saif",
            start_time_str="2026-09-01 14:00:00"
        )
        assert "scheduled" in res_event

        # Add Goal Tool
        goal_tool = AddGoalTool()
        res_goal = await goal_tool.execute(
            user_id=user_id,
            title="Save Money",
            target_value=1000.0,
            unit="USD"
        )
        assert "created" in res_goal

    # Verify directly from DB
    stmt_task = select(Task).where(Task.user_id == user_id, Task.title == "Read book")
    res_task_db = await db_session.execute(stmt_task)
    assert res_task_db.scalars().first() is not None

    stmt_event = select(Event).where(Event.user_id == user_id, Event.title == "Meeting with Saif")
    res_event_db = await db_session.execute(stmt_event)
    assert res_event_db.scalars().first() is not None

    stmt_goal = select(Goal).where(Goal.user_id == user_id, Goal.title == "Save Money")
    res_goal_db = await db_session.execute(stmt_goal)
    assert res_goal_db.scalars().first() is not None

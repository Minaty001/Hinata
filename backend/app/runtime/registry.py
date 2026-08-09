"""
Hinata Agent/Tool Runtime — Registry & Built-in Tools

Maintains discovery mappings and declares built-in system tools.
"""
from __future__ import annotations

import ast
import operator as op
from datetime import datetime
from typing import Any, Callable, Type, Optional
import logging
from pydantic import BaseModel, Field

from app.runtime.base import BaseTool
from app.api.websocket import manager as ws_manager

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Manages registered tools for agent selection and execution."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        if tool.name in self._tools:
            logger.warning("Overwriting registered tool: %s", tool.name)
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    def get(self, name: str) -> Optional[BaseTool]:
        """Lookup tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        """Return list of available tools with description and schema for LLM matching."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.args_schema.model_json_schema() if t.args_schema else {},
            }
            for t in self._tools.values()
        ]


# Central registry instance
registry = ToolRegistry()


def register_tool(cls: Type[BaseTool]) -> Type[BaseTool]:
    """Decorator to register a tool class."""
    registry.register(cls())
    return cls


# ── 1. Safe Calculator Tool ───────────────────────────────────────────────

class CalculatorInput(BaseModel):
    expression: str = Field(description="Math expression to evaluate, e.g. '2 + 2' or '(12 * 4) / 2'")


@register_tool
class CalculatorTool(BaseTool):
    name = "calculator"
    description = "Safe calculator to evaluate simple mathematical expressions."
    args_schema = CalculatorInput

    # Supported operators for safe AST evaluation
    _operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.USub: op.neg,
        ast.UAdd: op.pos,
    }

    def _eval(self, node) -> float:
        if isinstance(node, ast.Constant):  # Python >= 3.8
            return node.value
        elif isinstance(node, ast.BinOp):
            return self._operators[type(node.op)](self._eval(node.left), self._eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return self._operators[type(node.op)](self._eval(node.operand))
        else:
            raise TypeError(f"Unsupported mathematical syntax node: {type(node)}")

    async def execute(self, expression: str) -> str:
        """Parse and evaluate the math expression safely via AST."""
        try:
            # Strip spaces and validate characters to prevent malicious strings
            clean = expression.replace(" ", "")
            if not all(c in "0123456789+-*/()**." for c in clean):
                return "Error: Invalid characters in expression."
                
            node = ast.parse(clean, mode="eval").body
            result = self._eval(node)
            return str(result)
        except Exception as exc:
            return f"Error evaluating expression: {exc}"


# ── 2. Time Retrieval Tool ────────────────────────────────────────────────

class TimeInput(BaseModel):
    timezone_name: Optional[str] = Field(None, description="Timezone name, e.g. 'Asia/Kolkata' or 'UTC'")


@register_tool
class TimeTool(BaseTool):
    name = "get_time"
    description = "Get the current date and time."
    args_schema = TimeInput

    async def execute(self, timezone_name: Optional[str] = None) -> str:
        try:
            if timezone_name:
                import zoneinfo
                tz = zoneinfo.ZoneInfo(timezone_name)
                now = datetime.now(tz)
            else:
                now = datetime.now()
            return now.strftime("%Y-%m-%d %I:%M:%S %p %Z").strip()
        except Exception as exc:
            return f"Error getting time: {exc}"


# ── 3. Mock Weather Tool ──────────────────────────────────────────────────

class WeatherInput(BaseModel):
    location: str = Field(description="City or region name, e.g. 'New Delhi' or 'London'")


@register_tool
class WeatherTool(BaseTool):
    name = "get_weather"
    description = "Retrieve the current weather information for a location."
    args_schema = WeatherInput

    async def execute(self, location: str) -> str:
        # Mock weather database
        loc_clean = location.lower()
        if "delhi" in loc_clean or "kolkata" in loc_clean:
            return f"Weather in {location}: 32°C, Mostly Sunny. Humidity: 65%. Wind: 12 km/h."
        elif "london" in loc_clean:
            return f"Weather in {location}: 17°C, Light Drizzle. Humidity: 88%. Wind: 20 km/h."
        elif "tokyo" in loc_clean:
            return f"Weather in {location}: 22°C, Clear Sky. Humidity: 45%. Wind: 8 km/h."
        return f"Weather in {location}: 20°C, Partly Cloudy. Humidity: 50%. Wind: 10 km/h."


# ── 4. Web Search Tool ────────────────────────────────────────────────────

class SearchInput(BaseModel):
    query: str = Field(description="Search query terms")


@register_tool
class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the internet for real-time information or questions."
    args_schema = SearchInput

    async def execute(self, query: str) -> str:
        # Mocked web search for deterministic test runs
        return f"Search result for '{query}': Hinata platform is a production-quality AI companion rebuild."


# ── 5. Device Control Command Tool ────────────────────────────────────────

class DeviceActionInput(BaseModel):
    user_id: int = Field(description="User ID target of action")
    command: str = Field(description="Action name, e.g. 'android.volume_up' or 'android.flashlight'")
    arguments: Optional[dict[str, Any]] = Field(None, description="Arguments mapping for execution command")


@register_tool
class DeviceActionTool(BaseTool):
    name = "device_action"
    description = "Bridges conscious tool routing to active WebSocket client commands."
    args_schema = DeviceActionInput

    async def execute(self, user_id: int, command: str, arguments: Optional[dict[str, Any]] = None) -> str:
        payload = {
            "type": "command",
            "command": command,
            "arguments": arguments or {},
        }
        success = await ws_manager.send_to_user(user_id, payload)
        if success:
            return f"Command '{command}' successfully dispatched to user device WebSocket."
        return f"Command '{command}' registered, but client has no active WebSocket connection."


# ── 6. Productivity Add Task Tool ──────────────────────────────────────────

class AddTaskInput(BaseModel):
    user_id: int = Field(description="User ID target of action")
    title: str = Field(description="Task title")
    description: Optional[str] = Field(None, description="Optional task description details")
    due_date_str: Optional[str] = Field(None, description="Due date string in YYYY-MM-DD format")


@register_tool
class AddTaskTool(BaseTool):
    name = "add_task"
    description = "Add a personal productivity task or todo item for the user."
    args_schema = AddTaskInput

    async def execute(
        self,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        due_date_str: Optional[str] = None,
    ) -> str:
        from app.database.engine import AsyncSessionMaker
        from app.database.models import Task
        
        due_date = None
        if due_date_str:
            try:
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        due_date = datetime.strptime(due_date_str, fmt)
                        break
                    except ValueError:
                        continue
            except Exception:
                pass

        async with AsyncSessionMaker() as session:
            try:
                task = Task(
                    user_id=user_id,
                    title=title,
                    description=description,
                    due_date=due_date,
                    status="pending"
                )
                session.add(task)
                await session.commit()
                return f"Task '{title}' created successfully."
            except Exception as exc:
                return f"Error creating task: {exc}"


# ── 7. Productivity Add Event Tool ─────────────────────────────────────────

class AddEventInput(BaseModel):
    user_id: int = Field(description="User ID target of action")
    title: str = Field(description="Event title")
    description: Optional[str] = Field(None, description="Optional description of the event")
    start_time_str: str = Field(description="Start date and time string in YYYY-MM-DD HH:MM:SS format")
    location: Optional[str] = Field(None, description="Event location or link")


@register_tool
class AddEventTool(BaseTool):
    name = "add_event"
    description = "Schedule a reminder, event or appointment for the user."
    args_schema = AddEventInput

    async def execute(
        self,
        user_id: int,
        title: str,
        start_time_str: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
    ) -> str:
        from app.database.engine import AsyncSessionMaker
        from app.database.models import Event
        
        try:
            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                start_time = datetime.strptime(start_time_str, "%Y-%m-%d")
            except ValueError:
                return f"Error: Start time '{start_time_str}' does not match format YYYY-MM-DD HH:MM:SS."

        async with AsyncSessionMaker() as session:
            try:
                event = Event(
                    user_id=user_id,
                    title=title,
                    description=description,
                    start_time=start_time,
                    location=location,
                )
                session.add(event)
                await session.commit()
                return f"Event '{title}' scheduled at {start_time_str}."
            except Exception as exc:
                return f"Error scheduling event: {exc}"


# ── 8. Productivity Add Goal Tool ──────────────────────────────────────────

class AddGoalInput(BaseModel):
    user_id: int = Field(description="User ID target of action")
    title: str = Field(description="Goal title")
    target_value: float = Field(100.0, description="Target value metric to achieve")
    unit: Optional[str] = Field("%", description="Target metric unit, e.g. 'kg', 'km', '%'")


@register_tool
class AddGoalTool(BaseTool):
    name = "add_goal"
    description = "Create a long-term goal for the user to track progressive metrics."
    args_schema = AddGoalInput

    async def execute(
        self,
        user_id: int,
        title: str,
        target_value: float = 100.0,
        unit: Optional[str] = "%",
    ) -> str:
        from app.database.engine import AsyncSessionMaker
        from app.database.models import Goal

        async with AsyncSessionMaker() as session:
            try:
                goal = Goal(
                    user_id=user_id,
                    title=title,
                    target_value=target_value,
                    unit=unit,
                    current_value=0.0
                )
                session.add(goal)
                await session.commit()
                return f"Goal '{title}' created with target {target_value} {unit}."
            except Exception as exc:
                return f"Error creating goal: {exc}"

"""
Hinata Agent/Tool Runtime — Base Classes

Defines standard interfaces and metadata structure for tool execution.
"""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Encapsulates the output of a tool execution turn."""

    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class BaseTool:
    """Base class for all executable tools in the agent runtime."""

    name: str
    description: str
    args_schema: Optional[type[BaseModel]] = None

    async def execute(self, **kwargs) -> Any:
        """Core execution logic to be overridden by subclass."""
        raise NotImplementedError("Subclasses must implement execute")

"""
Hinata Agent/Tool Runtime — Safe Executor

Handles validation, sandbox execution monitoring, and execution time profiling.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import ValidationError

from app.runtime.base import ToolResult
from app.runtime.registry import registry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Safely executes registered system tools with schema validation."""

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> ToolResult:
        """Resolve and execute a tool by name with arguments validation."""
        start_time = time.perf_counter()
        tool = registry.get(name)

        if not tool:
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{name}' not found in registry",
                execution_time_ms=elapsed,
            )

        # Validate arguments against Pydantic schema
        validated_args = arguments
        if tool.args_schema:
            try:
                # Use model_validate for Pydantic v2 support
                parsed = tool.args_schema.model_validate(arguments)
                # Convert parsed model back to dictionary for function call unpacking
                validated_args = parsed.model_dump()
            except ValidationError as err:
                elapsed = (time.perf_counter() - start_time) * 1000.0
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Validation failed for tool '{name}': {err}",
                    execution_time_ms=elapsed,
                )

        # Execute inside safe boundaries
        try:
            output = await tool.execute(**validated_args)
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=True,
                output=output,
                execution_time_ms=elapsed,
            )
        except Exception as exc:
            logger.exception("Error executing tool '%s'", name)
            elapsed = (time.perf_counter() - start_time) * 1000.0
            return ToolResult(
                success=False,
                output=None,
                error=f"Execution failed: {exc}",
                execution_time_ms=elapsed,
            )

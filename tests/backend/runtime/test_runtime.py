"""
Tests for the Hinata Agent/Tool Runtime.

Verifies tool schema validation, AST evaluation safety, execution profiling,
and registry lookup.
"""
from __future__ import annotations

import pytest
from app.runtime.registry import registry
from app.runtime.executor import ToolExecutor


def test_tool_registration():
    """Verify built-in tools are correctly registered."""
    assert registry.get("calculator") is not None
    assert registry.get("get_time") is not None
    assert registry.get("get_weather") is not None
    assert registry.get("web_search") is not None
    assert registry.get("device_action") is not None


@pytest.mark.asyncio
async def test_calculator_execution_success():
    executor = ToolExecutor()
    
    # Simple add
    res1 = await executor.execute("calculator", {"expression": "2 + 2"})
    assert res1.success
    assert res1.output == "4"

    # Multi operators with parentheses
    res2 = await executor.execute("calculator", {"expression": "(12 * 4) / (2 + 6)"})
    assert res2.success
    assert res2.output == "6.0"

    # Negatives
    res3 = await executor.execute("calculator", {"expression": "-5 * 4"})
    assert res3.success
    assert res3.output == "-20"


@pytest.mark.asyncio
async def test_calculator_execution_safety_rejection():
    executor = ToolExecutor()

    # Rejected due to illegal characters (e.g. letters / print)
    res1 = await executor.execute("calculator", {"expression": "__import__('os').system('ls')"})
    assert res1.success
    assert "Invalid characters" in res1.output

    # Rejected due to letters in expression
    res2 = await executor.execute("calculator", {"expression": "2 + a"})
    assert res2.success
    assert "Invalid characters" in res2.output


@pytest.mark.asyncio
async def test_time_tool_execution():
    executor = ToolExecutor()
    res = await executor.execute("get_time", {})
    assert res.success
    assert ":" in res.output


@pytest.mark.asyncio
async def test_executor_validation_failure():
    executor = ToolExecutor()
    # Missing required 'expression' argument for calculator
    res = await executor.execute("calculator", {})
    assert not res.success
    assert "Validation failed" in res.error


@pytest.mark.asyncio
async def test_executor_missing_tool():
    executor = ToolExecutor()
    res = await executor.execute("non_existent_tool_xyz", {"arg": 1})
    assert not res.success
    assert "not found in registry" in res.error

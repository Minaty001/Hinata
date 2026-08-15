"""
Tests for /api/v1/memory endpoints.
Uses in-memory database via conftest.py fixtures.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_list_memories_empty(client: AsyncClient):
    res = await client.get("/api/v1/memory/")
    assert res.status_code == 200
    body = res.json()
    assert "memories" in body
    assert body["total"] == 0


async def test_create_memory(client: AsyncClient):
    res = await client.post(
        "/api/v1/memory/",
        json={"type": "fact", "content": "I like coffee", "importance": 3},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["content"] == "I like coffee"
    assert body["type"] == "fact"
    assert body["importance"] == 3


async def test_create_memory_shows_in_list(client: AsyncClient):
    await client.post(
        "/api/v1/memory/",
        json={"type": "preference", "content": "Prefers dark mode", "importance": 4},
    )
    res = await client.get("/api/v1/memory/")
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["memories"][0]["content"] == "Prefers dark mode"


async def test_delete_memory(client: AsyncClient):
    create_res = await client.post(
        "/api/v1/memory/",
        json={"type": "goal", "content": "Learn piano", "importance": 5},
    )
    memory_id = create_res.json()["id"]
    del_res = await client.delete(f"/api/v1/memory/{memory_id}")
    assert del_res.status_code == 200

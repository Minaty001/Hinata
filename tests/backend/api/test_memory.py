"""
Tests for /api/v1/memory endpoints.
Uses in-memory database via conftest.py fixtures.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.backend.conftest import create_test_account


pytestmark = pytest.mark.asyncio


async def _login(client: AsyncClient, username: str) -> str:
    await create_test_account(username)
    response = await client.post("/api/v1/auth/login", json={"username": username, "password": "password123"})
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_list_memories_requires_auth(client: AsyncClient):
    res = await client.get("/api/v1/memory/")
    assert res.status_code == 401


async def test_list_memories_empty(client: AsyncClient):
    token = await _login(client, "mem_user_1")
    res = await client.get(
        "/api/v1/memory/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "memories" in body
    assert body["total"] == 0


async def test_create_memory(client: AsyncClient):
    token = await _login(client, "mem_user_2")
    res = await client.post(
        "/api/v1/memory/",
        json={"type": "fact", "content": "I like coffee", "importance": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["content"] == "I like coffee"
    assert body["type"] == "fact"
    assert body["importance"] == 3


async def test_create_memory_shows_in_list(client: AsyncClient):
    token = await _login(client, "mem_user_3")
    await client.post(
        "/api/v1/memory/",
        json={"type": "preference", "content": "Prefers dark mode", "importance": 4},
        headers={"Authorization": f"Bearer {token}"},
    )
    res = await client.get(
        "/api/v1/memory/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["memories"][0]["content"] == "Prefers dark mode"


async def test_delete_memory(client: AsyncClient):
    token = await _login(client, "mem_user_4")
    create_res = await client.post(
        "/api/v1/memory/",
        json={"type": "goal", "content": "Learn piano", "importance": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    memory_id = create_res.json()["id"]
    del_res = await client.delete(
        f"/api/v1/memory/{memory_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200


async def test_cannot_access_other_users_memories(client: AsyncClient):
    token1 = await _login(client, "mem_user_5a")
    token2 = await _login(client, "mem_user_5b")
    # User 1 creates a memory
    create_res = await client.post(
        "/api/v1/memory/",
        json={"type": "fact", "content": "secret", "importance": 5},
        headers={"Authorization": f"Bearer {token1}"},
    )
    memory_id = create_res.json()["id"]
    # User 2 tries to delete user 1's memory
    del_res = await client.delete(
        f"/api/v1/memory/{memory_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert del_res.status_code in (403, 404)


async def test_memory_isolation_between_users(client: AsyncClient):
    """User A's memories must not appear in User B's list."""
    token_a = await _login(client, "mem_user_6a")
    token_b = await _login(client, "mem_user_6b")

    # User A creates a memory
    await client.post(
        "/api/v1/memory/",
        json={"type": "fact", "content": "User A secret", "importance": 1},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User B lists their memories — should be empty
    res = await client.get(
        "/api/v1/memory/",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res.status_code == 200
    assert res.json()["total"] == 0

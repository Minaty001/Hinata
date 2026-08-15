"""
Tests for no-auth default-user behavior after login/register removal.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_me_without_token_returns_local_user(client: AsyncClient):
    res = await client.get("/api/v1/users/me")
    assert res.status_code == 200
    body = res.json()
    assert body["username"] == "local"


async def test_chat_without_token(client: AsyncClient):
    res = await client.post("/api/v1/chat/", json={"message": "hello"})
    assert res.status_code == 200
    body = res.json()
    assert "reply" in body
    assert "chain_id" in body


async def test_memory_without_token(client: AsyncClient):
    res = await client.get("/api/v1/memory/")
    assert res.status_code == 200
    assert res.json()["total"] == 0


async def test_auth_router_gone(client: AsyncClient):
    res = await client.post("/api/v1/auth/login", json={"username": "x", "password": "y"})
    assert res.status_code in (404, 405)

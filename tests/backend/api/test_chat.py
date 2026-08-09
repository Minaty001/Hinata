"""
Tests for /api/v1/chat endpoints.
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


async def test_chat_requires_auth(client: AsyncClient):
    res = await client.post(
        "/api/v1/chat/",
        json={"message": "hello"},
    )
    assert res.status_code == 401


async def test_chat_with_auth(client: AsyncClient):
    token = await _login(client, "chat_user_1")
    res = await client.post(
        "/api/v1/chat/",
        json={"message": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "reply" in body
    assert "chain_id" in body


async def test_chat_persists_chain_id(client: AsyncClient):
    token = await _login(client, "chat_user_2")
    # First message creates a chain
    res1 = await client.post(
        "/api/v1/chat/",
        json={"message": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    chain_id = res1.json()["chain_id"]

    # Second message in same chain
    res2 = await client.post(
        "/api/v1/chat/",
        json={"message": "how are you?", "chain_id": chain_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 200
    assert res2.json()["chain_id"] == chain_id


async def test_get_chains_requires_auth(client: AsyncClient):
    res = await client.get("/api/v1/chat/chains")
    assert res.status_code == 401


async def test_get_chains_with_auth(client: AsyncClient):
    token = await _login(client, "chat_user_3")
    # Create a chat to have at least one chain
    await client.post(
        "/api/v1/chat/",
        json={"message": "hello"},
        headers={"Authorization": f"Bearer {token}"},
    )
    res = await client.get(
        "/api/v1/chat/chains",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1


async def test_create_chain(client: AsyncClient):
    token = await _login(client, "chat_user_4")
    res = await client.post(
        "/api/v1/chat/chains",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "chain_id" in body
    assert "title" in body


async def test_delete_chain(client: AsyncClient):
    token = await _login(client, "chat_user_5")
    # Create a chain
    create_res = await client.post(
        "/api/v1/chat/chains",
        headers={"Authorization": f"Bearer {token}"},
    )
    chain_id = create_res.json()["chain_id"]
    # Delete it
    del_res = await client.delete(
        f"/api/v1/chat/chains/{chain_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200


async def test_cannot_delete_other_users_chain(client: AsyncClient):
    token1 = await _login(client, "chat_user_6a")
    token2 = await _login(client, "chat_user_6b")
    # User 1 creates a chain
    create_res = await client.post(
        "/api/v1/chat/chains",
        headers={"Authorization": f"Bearer {token1}"},
    )
    chain_id = create_res.json()["chain_id"]
    # User 2 tries to delete it
    del_res = await client.delete(
        f"/api/v1/chat/chains/{chain_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert del_res.status_code == 404


async def test_get_history(client: AsyncClient):
    token = await _login(client, "chat_user_7")
    # Chat to populate history
    chat_res = await client.post(
        "/api/v1/chat/",
        json={"message": "test message"},
        headers={"Authorization": f"Bearer {token}"},
    )
    chain_id = chat_res.json()["chain_id"]
    # Get history
    hist_res = await client.get(
        f"/api/v1/chat/chains/{chain_id}/history",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert hist_res.status_code == 200
    body = hist_res.json()
    assert body["chain_id"] == chain_id
    assert len(body["messages"]) >= 2  # user + assistant

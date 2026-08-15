"""
Tests for /api/v1/chat endpoints.
Uses in-memory database via conftest.py fixtures.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_chat_without_token(client: AsyncClient):
    res = await client.post(
        "/api/v1/chat/",
        json={"message": "hello"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "reply" in body
    assert "chain_id" in body


async def test_chat_persists_chain_id(client: AsyncClient):
    # First message creates a chain
    res1 = await client.post(
        "/api/v1/chat/",
        json={"message": "hello"},
    )
    chain_id = res1.json()["chain_id"]

    # Second message in same chain
    res2 = await client.post(
        "/api/v1/chat/",
        json={"message": "how are you?", "chain_id": chain_id},
    )
    assert res2.status_code == 200
    assert res2.json()["chain_id"] == chain_id


async def test_get_chains(client: AsyncClient):
    # Create a chat to have at least one chain
    await client.post(
        "/api/v1/chat/",
        json={"message": "hello"},
    )
    res = await client.get("/api/v1/chat/chains")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 1


async def test_create_chain(client: AsyncClient):
    res = await client.post("/api/v1/chat/chains")
    assert res.status_code == 200
    body = res.json()
    assert "chain_id" in body
    assert "title" in body


async def test_delete_chain(client: AsyncClient):
    # Create a chain
    create_res = await client.post("/api/v1/chat/chains")
    chain_id = create_res.json()["chain_id"]
    # Delete it
    del_res = await client.delete(f"/api/v1/chat/chains/{chain_id}")
    assert del_res.status_code == 200


async def test_get_history(client: AsyncClient):
    # Chat to populate history
    chat_res = await client.post(
        "/api/v1/chat/",
        json={"message": "test message"},
    )
    chain_id = chat_res.json()["chain_id"]
    # Get history
    hist_res = await client.get(f"/api/v1/chat/chains/{chain_id}/history")
    assert hist_res.status_code == 200
    body = hist_res.json()
    assert body["chain_id"] == chain_id
    assert len(body["messages"]) >= 2  # user + assistant

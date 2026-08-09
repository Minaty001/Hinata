"""
Tests for /api/v1/auth endpoints.
Uses in-memory database via conftest.py fixtures.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser_reg", "password": "password123"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_register_duplicate_username(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser_dup", "password": "password123"},
    )
    res = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser_dup", "password": "password123"},
    )
    assert res.status_code == 400
    assert "already taken" in res.json()["detail"].lower()


async def test_register_password_too_short(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser_short", "password": "123"},
    )
    assert res.status_code == 400


async def test_register_username_too_short(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={"username": "ab", "password": "password123"},
    )
    assert res.status_code == 400


async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "logintest_ok", "password": "password123"},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"username": "logintest_ok", "password": "password123"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "logintest_wrong", "password": "password123"},
    )
    res = await client.post(
        "/api/v1/auth/login",
        json={"username": "logintest_wrong", "password": "wrongpassword"},
    )
    assert res.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/login",
        json={"username": "nobody_xyz", "password": "password123"},
    )
    assert res.status_code == 401


async def test_get_me_unauthenticated(client: AsyncClient):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401


async def test_get_me_authenticated(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": "metest_auth", "password": "password123"},
    )
    token = reg.json()["access_token"]
    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "id" in body
    assert body["username"] == "metest_auth"


async def test_refresh_token(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": "refreshtest_ok", "password": "password123"},
    )
    refresh = reg.json()["refresh_token"]
    res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_refresh_token_reuse_fails(client: AsyncClient):
    """After refresh, old refresh token must be revoked."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": "refreshtest_reuse", "password": "password123"},
    )
    old_refresh = reg.json()["refresh_token"]

    # First refresh works
    await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

    # Second use of same refresh token must fail
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert res.status_code == 401


async def test_logout(client: AsyncClient):
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": "logouttest_ok", "password": "password123"},
    )
    token = reg.json()["access_token"]
    res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

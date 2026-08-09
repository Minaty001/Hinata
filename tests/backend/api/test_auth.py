"""
Tests for /api/v1/auth endpoints.
Uses in-memory database via conftest.py fixtures.
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from tests.backend.conftest import create_test_account


pytestmark = pytest.mark.asyncio


async def test_public_registration_is_unavailable(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={"username": "testuser_reg", "password": "password123"},
    )
    assert res.status_code == 404


async def test_login_success(client: AsyncClient):
    await create_test_account("logintest_ok")
    res = await client.post(
        "/api/v1/auth/login",
        json={"username": "logintest_ok", "password": "password123"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


async def test_login_wrong_password(client: AsyncClient):
    await create_test_account("logintest_wrong")
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
    await create_test_account("metest_auth")
    login = await client.post("/api/v1/auth/login", json={"username": "metest_auth", "password": "password123"})
    token = login.json()["access_token"]
    res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "id" in body
    assert body["username"] == "metest_auth"


async def test_refresh_token(client: AsyncClient):
    await create_test_account("refreshtest_ok")
    login = await client.post("/api/v1/auth/login", json={"username": "refreshtest_ok", "password": "password123"})
    refresh = login.json()["refresh_token"]
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
    await create_test_account("refreshtest_reuse")
    login = await client.post("/api/v1/auth/login", json={"username": "refreshtest_reuse", "password": "password123"})
    old_refresh = login.json()["refresh_token"]

    # First refresh works
    await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

    # Second use of same refresh token must fail
    res = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert res.status_code == 401


async def test_logout(client: AsyncClient):
    await create_test_account("logouttest_ok")
    login = await client.post("/api/v1/auth/login", json={"username": "logouttest_ok", "password": "password123"})
    token = login.json()["access_token"]
    res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200

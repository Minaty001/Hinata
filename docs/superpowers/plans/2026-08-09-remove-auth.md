# Remove Login + Register — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the login/register system (backend functions + web UI) and replace it with a single local default user, with all data stored in the existing SQLite DB.

**Architecture:** The `/api/v1/auth/*` router, JWT/bcrypt code, and the web login modal are deleted. `get_current_user` becomes a no-auth dependency that always resolves one fixed `User` row (`username="local"`), created lazily on first request and eagerly at startup. The WebSocket connects as that same user. The Telegram bot and the `Account`/`UserSession`/`Identity` models are untouched.

**Tech Stack:** Python 3.14, FastAPI, SQLAlchemy 2 async (aiosqlite), pytest/pytest-asyncio/httpx, plain JS + HTML web app.

**Spec:** `docs/superpowers/specs/2026-08-09-remove-auth-design.md`

## Global Constraints

- Default user identity is `User(username="local")` — fixed string, used verbatim.
- Telegram bot is out of scope: do NOT modify `app.py` (repo root), `bot.py`, `handlers/*`.
- `Account`, `UserSession`, `Identity` models stay in `backend/app/database/models.py` — do not edit that file.
- Do NOT touch `tests/test_multi_provider.py` (pre-existing collection failure unrelated to auth — it only fails when pytest runs the whole `tests/` dir from the repo root; always run `python3 -m pytest tests/backend -q` from `/root/Hinata`).
- All tests run with the in-memory DB from `tests/backend/conftest.py`; never touch the real `data/hinata.db`.
- Web app must load straight into chat: no modal, no `Authorization` header, no `hinata_token` in localStorage.
- Working dir for all backend commands: `/root/Hinata`.

---

### Task 1: Remove backend auth — default user, delete auth router/schemas, migrate tests

**Files:**
- Rewrite: `backend/app/core/security.py` (currently 70 lines)
- Delete: `backend/app/api/auth.py`
- Delete: `backend/app/schemas/auth.py`
- Modify: `backend/app/main.py`
- Modify: `tests/backend/conftest.py`
- Delete: `tests/backend/api/test_auth.py`
- Rewrite: `tests/backend/api/test_chat.py`, `tests/backend/api/test_memory.py`
- Modify: `tests/backend/productivity/test_productivity.py`, `tests/backend/voice/test_voice.py`, `tests/backend/reflex/test_reflex.py`
- Create: `tests/backend/api/test_default_user.py`

**Interfaces:**
- Consumes: nothing new (uses existing `app.database.engine.AsyncSessionMaker` / `get_session`, `app.database.models.User`).
- Produces (used by Task 2):
  - `get_default_user(session: AsyncSession) -> User` in `app.core.security`
  - `ensure_default_user() -> None` in `app.core.security`
  - `get_current_user(session: AsyncSession = Depends(get_session)) -> User` — no-auth dependency, returns the default user
  - `get_current_user_optional(session: AsyncSession = Depends(get_session)) -> User` — same (kept for API stability)

- [ ] **Step 1: Write the failing tests**

Create `tests/backend/api/test_default_user.py`:

```python
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
    assert res.status_code == 404
```

- [ ] **Step 2: Run the new tests to verify they fail**

Run: `cd /root/Hinata && python3 -m pytest tests/backend/api/test_default_user.py -q`
Expected: 4 FAILED — the first three get 401 (auth still enforced), the last gets 401 instead of 404 (router still exists).

- [ ] **Step 3: Rewrite `backend/app/core/security.py`**

Replace the entire file with:

```python
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.engine import AsyncSessionMaker, get_session
from app.database.models import User

DEFAULT_USER_USERNAME = "local"


async def get_default_user(session: AsyncSession) -> User:
    """Return the single local user, creating it lazily if missing."""
    result = await session.execute(
        select(User).where(User.username == DEFAULT_USER_USERNAME)
    )
    user = result.scalars().first()
    if user is None:
        user = User(username=DEFAULT_USER_USERNAME, display_name="Local User")
        session.add(user)
        await session.flush()
    return user


async def ensure_default_user() -> None:
    """Create the local default user at startup if it does not exist yet."""
    async with AsyncSessionMaker() as session:
        await get_default_user(session)
        await session.commit()


async def get_current_user(session: AsyncSession = Depends(get_session)) -> User:
    """No-auth dependency: always resolves the single local user."""
    return await get_default_user(session)


async def get_current_user_optional(session: AsyncSession = Depends(get_session)) -> User:
    """No-auth dependency: same as get_current_user (kept for API stability)."""
    return await get_default_user(session)
```

This removes: `passlib`, `jose`, `bcrypt`, `OAuth2PasswordBearer`, `hash_password`, `verify_password`, `create_access_token`, `create_refresh_token`, `decode_token`, `oauth2_scheme`.

- [ ] **Step 4: Delete the auth API and schemas**

```bash
rm backend/app/api/auth.py backend/app/schemas/auth.py
```

- [ ] **Step 5: Update `backend/app/main.py`**

- Replace line 14 `from app.api.auth import ensure_bootstrap_admin, router as auth_router` with:

```python
from app.core.security import ensure_default_user
```

- Replace line 28 `await ensure_bootstrap_admin()` with:

```python
    await ensure_default_user()
```

- Delete line 48 `app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])`.

- Update the comment above the static mount (lines 61-62) from:

```python
# Register the static site after API and health routes so the sign-in client
# and its authenticated API calls are served from the same public origin.
```

to:

```python
# Register the static site after API and health routes so the web client and
# its API calls are served from the same public origin.
```

- [ ] **Step 6: Update `tests/backend/conftest.py`**

- Delete line 25 `os.environ.setdefault("JWT_SECRET", "test_secret_key_32_chars_minimum_here")`.
- Delete line 29-30 imports `from app.database.models import Account, User` and `from app.core.security import hash_password`.
- Delete the whole `create_test_account` function (lines 41-56).

- [ ] **Step 7: Delete `tests/backend/api/test_auth.py`**

```bash
rm tests/backend/api/test_auth.py
```

- [ ] **Step 8: Rewrite `tests/backend/api/test_chat.py`**

Replace the entire file with (login helpers, auth headers, and the cross-user isolation test are gone):

```python
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
```

- [ ] **Step 9: Rewrite `tests/backend/api/test_memory.py`**

Replace the entire file with:

```python
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
```

- [ ] **Step 10: Update `tests/backend/productivity/test_productivity.py`**

- Replace the `_login` helper (lines 29-38) with:

```python
async def _current_user_id(client: AsyncClient) -> int:
    """Fetch the single local user's id from /api/v1/users/me (no auth)."""
    me = await client.get("/api/v1/users/me")
    assert me.status_code == 200
    return me.json()["id"]
```

- In each of the 4 tests, replace the first two lines `token, user_id = await _login(client, "...")` / `headers = {"Authorization": f"Bearer {token}"}` with `user_id = await _current_user_id(client)` and delete every `headers=headers,` / `headers=headers` argument from the request calls. The `test_productivity_runtime_tools` test keeps its `user_id` local variable (used for the DB assertions) — only the login/header lines change.

- [ ] **Step 11: Update `tests/backend/voice/test_voice.py`**

- Delete the `_login` helper (lines 16-20) and the `from tests.backend.conftest import create_test_account` import (line 13).
- In each of the 3 tests, delete `token = await _login(client, "...")` and `headers = {"Authorization": f"Bearer {token}"}`, and remove the `headers=headers,` argument from each request call.

- [ ] **Step 12: Update `tests/backend/reflex/test_reflex.py`**

- Delete the `from tests.backend.conftest import create_test_account` import (line 11).
- In `test_reflex_execution_integration` (lines 72-93), delete the `create_test_account` + login block (lines 75-81) and the `headers={"Authorization": f"Bearer {token}"}` argument on the POST; the request becomes:

```python
    # Send a reflex query to the chat endpoint
    res = await client.post(
        "/api/v1/chat/",
        json={"message": "flashlight off"},
    )
```

- [ ] **Step 13: Run the full backend suite**

Run: `cd /root/Hinata && python3 -m pytest tests/backend -q`
Expected: ALL PASS (previously 51; after removal the count differs but every test must pass).

- [ ] **Step 14: Commit**

```bash
git add -A backend tests
git commit -m "feat: remove backend login/register — single default local user"
```

---

### Task 2: WebSocket connects as the default user (no token)

**Files:**
- Rewrite: `backend/app/api/websocket.py`
- Create: `tests/backend/api/test_websocket.py`

**Interfaces:**
- Consumes: `get_default_user(session: AsyncSession) -> User` from `app.core.security` (Task 1), `AsyncSessionMaker` from `app.database.engine`.
- Produces: `/ws` endpoint that accepts any connection and registers it under the default user's id.

- [ ] **Step 1: Write the failing test**

Create `tests/backend/api/test_websocket.py`:

```python
"""
Tests for the /ws WebSocket endpoint (no-auth default user).
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_ws_connects_without_token(client: AsyncClient):
    async with client.websocket_connect("/ws") as ws:
        await ws.send_json({"type": "ping"})
        response = await ws.receive_json()
        assert response == {"type": "pong"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd /root/Hinata && python3 -m pytest tests/backend/api/test_websocket.py -q`
Expected: FAIL — the endpoint closes with WS_1008 because no token is supplied.

- [ ] **Step 3: Rewrite `backend/app/api/websocket.py`**

Replace the entire file with:

```python
"""
Hinata Backend — WebSocket Manager & Connection Registry

Maintains persistent duplex connections for real-time streaming, pairing, and
direct device-control command dispatch.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import get_default_user
from app.database.engine import AsyncSessionMaker

logger = logging.getLogger(__name__)
router = APIRouter()


class WebSocketConnectionManager:
    """Manages active WebSocket connections keyed by the default user ID."""

    def __init__(self) -> None:
        # Map user_id -> set of active WebSocket instances
        self.active_connections: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Accept connection and register it in memory."""
        await websocket.accept()
        self.active_connections.setdefault(user_id, set()).add(websocket)
        logger.info("WebSocket connected for user_id=%d. Total active sockets: %d", user_id, len(self.active_connections[user_id]))

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Deregister active connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info("WebSocket disconnected for user_id=%d", user_id)

    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> bool:
        """Send JSON payload to all active WebSocket connections for a user.

        Returns True if at least one message was sent successfully.
        """
        sockets = self.active_connections.get(user_id, set())
        if not sockets:
            logger.warning("No active WebSocket connections found for user_id=%d", user_id)
            return False

        success = False
        message_str = json.dumps(payload)
        for ws in list(sockets):
            try:
                await ws.send_text(message_str)
                success = True
            except Exception as exc:
                logger.error("Failed to send socket payload to user_id=%d: %s", user_id, exc)
                self.disconnect(user_id, ws)
        return success


manager = WebSocketConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Duplex WebSocket endpoint — always connects as the local default user."""
    async with AsyncSessionMaker() as db_session:
        user = await get_default_user(db_session)
        await db_session.commit()
        user_id = user.id

    await manager.connect(user_id, websocket)
    try:
        while True:
            # Maintain connection, handle incoming client messages (e.g. heartbeat or confirmations)
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
                logger.debug("Received WebSocket data from user_id=%d: %s", user_id, data)

                # Echo check or keepalive ping-pong
                if data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                # Fallback echo for legacy standard text clients
                await websocket.send_text(f"Echo: {data_str}")
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as exc:
        logger.error("Error in WebSocket thread for user_id=%d: %s", user_id, exc)
        manager.disconnect(user_id, websocket)
```

This removes: `decode_token`, the `token` query param, the `UserSession` lookup, and all WS_1008 rejections.

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd /root/Hinata && python3 -m pytest tests/backend/api/test_websocket.py -q`
Expected: PASS.

- [ ] **Step 5: Run the full backend suite**

Run: `cd /root/Hinata && python3 -m pytest tests/backend -q`
Expected: ALL PASS.

- [ ] **Step 6: Commit**

```bash
git add -A backend tests
git commit -m "feat: websocket connects as default user without token"
```

---

### Task 3: Remove the login UI and token handling from the web app

**Files:**
- Modify: `web/index.html` (remove Logout button line 117, remove auth modal lines 587-608)
- Modify: `web/app.js` (remove auth block lines 6-93, remove token gate lines 808-820, rename `authFetch` → `fetch` at 10 call sites)

**Interfaces:**
- Consumes: the no-auth API from Tasks 1-2 (endpoints require no token).
- Produces: a web app that loads straight into chat with no modal, no `Authorization` header, no `hinata_token` localStorage key.

- [ ] **Step 1: Remove the Logout button from `web/index.html`**

Delete line 117:

```html
                <button class="btn btn-sm btn-outline btn-logout-action" id="btnLogout" style="font-size: 0.75rem; padding: 4px 10px;">Logout</button>
```

- [ ] **Step 2: Remove the auth modal from `web/index.html`**

Delete lines 587-608, i.e. from the `<!-- Premium Auth Modal Backdrop (Glow & Glassmorphism) -->` comment through the modal's closing `</div>` on line 608 (the block starting at `<div class="modal-backdrop active" id="authModal" ...>`). Leave line 585 `</div>` (memory modal close) and line 610 `<!-- Toast Notification Container -->` intact.

- [ ] **Step 3: Remove the auth/token block from `web/app.js`**

Delete lines 6-93: from `// --- 🌸 HINATA AUTHENTICATION & NATIVE CONTROL STATE 🌸 ---` through the closing `}` of `initAfterAuth()` (includes `jwtToken`, `authModal`/`authUsernameInput`/`authPasswordInput`/`btnLogout` consts, the login submit handler, the logout handler, the `authFetch` wrapper, and `initAfterAuth`). Keep line 5 (`document.addEventListener('DOMContentLoaded', () => {`) and everything from line 95 onward (`window.onBatteryStatus = ...`).

- [ ] **Step 4: Replace the startup token gate in `web/app.js`**

Replace lines 808-820 (the `// Verify token session and load config` if/else block) with:

```js
  // Load backend configs and chat data on startup (no auth required)
  loadChains();
  loadMemoriesFromBackend();
  loadProvidersFromBackend();

  // Query native battery level status if running on dynamic Android client shell
  if (window.HinataDeviceBridge) {
    window.HinataDeviceBridge.postMessage(JSON.stringify({
      command: 'android.battery_status'
    }));
  }
```

- [ ] **Step 5: Replace `authFetch` with `fetch` in `web/app.js`**

Replace `authFetch(` with `fetch(` at exactly these 10 call sites (lines 551, 615, 633, 660, 703, 836, 908, 982, 1035, 1170). Do not rename anything else — the calls take identical arguments.

- [ ] **Step 6: Syntax-check the JavaScript**

Run: `node --check web/app.js`
Expected: no output, exit code 0. (If `node` is unavailable, skip and rely on Step 7's grep + the browser smoke test in Task 4.)

- [ ] **Step 7: Verify no auth leftovers in the web app**

Run: `cd /root/Hinata && grep -rn -E "authFetch|jwtToken|authModal|hinata_token|btnLogout|btnSubmitAuth|/api/v1/auth" web/ --include="*.js" --include="*.html"`
Expected: no matches. (`.auth-tab-btn` in `web/style.css` is leftover CSS and is acceptable to leave; it must not be flagged by this grep since the pattern does not match it.)

- [ ] **Step 8: Run the backend suite (sanity — web change must not affect it)**

Run: `cd /root/Hinata && python3 -m pytest tests/backend -q`
Expected: ALL PASS.

- [ ] **Step 9: Commit**

```bash
git add web/index.html web/app.js
git commit -m "feat: remove login UI and token handling from web app"
```

---

### Task 4: Smoke test and push

**Files:**
- None (verification only; commit any fixes the smoke test surfaces as part of the relevant task's file set).

**Interfaces:**
- Consumes: the finished backend (Tasks 1-2) and web app (Task 3).

- [ ] **Step 1: Run the full backend test suite**

Run: `cd /root/Hinata && python3 -m pytest tests/backend -q`
Expected: ALL PASS.

- [ ] **Step 2: Boot the server and smoke-test the API**

```bash
cd /root/Hinata/backend && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/hinata-smoke.log 2>&1 &
sleep 4
```

Then verify, in order:

```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/health        # expect 200
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"x","password":"y"}'   # expect 404
curl -s http://127.0.0.1:8000/api/v1/users/me                              # expect {"id":1,"username":"local",...}
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/chat/chains   # expect 200
```

Expected: `200`, `404`, a JSON body with `"username":"local"`, `200`. Kill the server afterwards (`kill %1` or `pkill -f "uvicorn app.main:app"`).

- [ ] **Step 3: Check the Flutter app for stray auth references**

Run: `cd /root/Hinata && grep -rn -i -E "api/v1/auth|bearer|hinata_token" flutter_app/lib/ || true`
Expected: no matches. (If matches appear, report them — do not modify Flutter code without asking.)

- [ ] **Step 4: Push to git**

```bash
git status --short   # confirm working tree contains only intended changes
git push origin master
```

Expected: push succeeds, `origin` = `github.com/Minaty001/Hinata`.

- [ ] **Step 5: Report completion**

Summarize for the user: auth fully removed (endpoints, JWT/bcrypt, modal), single local user in DB, test counts, smoke-test results, and the pushed commit(s).

---

## Self-Review Notes (filled in by plan author)

1. **Spec coverage:** backend removal (Task 1), websocket (Task 2), frontend (Task 3), verification incl. flutter grep + push (Task 4). All spec sections map to a task.
2. **Placeholder scan:** no TBD/TODO; every code step contains full code.
3. **Type consistency:** `get_default_user(session) -> User` and `ensure_default_user()` names/imports match across Tasks 1-2; `_current_user_id` helper returns `int` used only as `user_id`; no cross-task signature drift.

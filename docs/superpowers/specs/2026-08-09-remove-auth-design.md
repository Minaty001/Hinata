# Remove Login + Register: Design Spec

- **Date:** 2026-08-09
- **Status:** Approved
- **Scope:** Remove the login/register system (backend functions and web UI), replace it with a single local default user, and store data in the existing SQLite DB.

## Context

The app previously had a web auth system: `/api/v1/auth/*` endpoints (login, refresh, logout, me, telegram link) issuing JWTs, a signup flow, and a login modal in the web UI. Signup was already removed (commit `9f98e5e`). This change removes login entirely.

Every non-auth API endpoint (chat, memory, settings, productivity, voice) and the `/ws` websocket key all data off `user_id`. After removing auth, the system must still resolve a user for these endpoints.

## Decisions (confirmed with user)

1. **Single default local user.** The backend auto-creates one fixed local `User` row on startup; every API request and the websocket resolve to that user. No login, no JWT, no sessions.
2. **Delete the auth API + UI; keep the auth tables.** The `Account`, `UserSession`, and `Identity` models/tables stay dormant (SQLAlchemy `create_all` never drops tables, so existing DBs keep them harmlessly).
3. **Telegram bot untouched.** The bot's separate `User` rows, auto-registration in `handlers/message_handler.py`, and admin commands are out of scope.

## Backend changes (`backend/app/`)

### `core/security.py`

- Delete: `oauth2_scheme`, `create_access_token`, `create_refresh_token`, `decode_token`, `hash_password`, `verify_password` (bcrypt/python-jose imports go with them).
- Rewire `get_current_user` and `get_current_user_optional` to take no token — both resolve the default user via `get_default_user(session)`.
- Add `get_default_user(session)`:
  - Looks up the `User` row with the fixed local identity (e.g. `username="local"`).
  - **Lazily creates it if missing** (defensive — a request never fails on identity).

### `api/auth.py`

Delete the entire router: `/login`, `/refresh`, `/logout`, `/me`, `/telegram/link`, plus `_create_account` and `ensure_bootstrap_admin`.

### `schemas/auth.py`

Delete the file (its `Optional`/pydantic import gotcha disappears with it). Confirm no other module imports from it.

### `main.py`

- Lifespan: remove `ensure_bootstrap_admin()`, add `ensure_default_user()`.
- Remove the auth router include.

### `api/websocket.py`

Remove the JWT check (token query param / header, `decode_token`, `UserSession` jti lookup, WS_1008 rejection). The socket connects directly as the default user.

### `database/models.py`

No changes — `Account`/`UserSession`/`Identity` stay dormant; `User` stays (bot + default user). `init_db()`/`create_all` untouched.

## Data flow

1. App starts → `ensure_default_user()` creates/fetches the fixed local `User` row.
2. Browser loads the web app → no modal, no stored token.
3. Frontend calls `fetch('/api/v1/chat/…')` etc. with no `Authorization` header.
4. `get_current_user` dependency returns the default user; all queries run under that `user_id`.
5. `/ws` connects as the default user.

## Frontend changes (`web/`)

### `index.html`

Delete the `#authModal` markup (and any auth-only styles/scripts bound to it).

### `app.js`

- Delete: `jwtToken` (line ~7), the login form handler (~line 28), logout handler, `authFetch` wrapper (~line 63), and the 401 → clear token → reopen modal logic.
- Replace all ~15 `authFetch` call sites with plain `fetch`.
- Remove the `initAfterAuth()` gate and the DOMContentLoaded token check — load chat/init functions directly on page load.

## Error handling

- No auth errors remain; all 401-handling paths are deleted. Existing 404/500 handling stays.
- If the default user row is ever missing, `get_default_user` recreates it on first request — no identity failure path.

## Testing / verification

- Delete `tests/backend/api/test_auth.py`; add a small replacement test asserting chat/memory endpoints return 200 **without any token**.
- Update any other backend tests that pass auth headers / create tokens.
- Run `python3 -m pytest tests/backend -q` → all green (baseline: 51 passed).
- Smoke test: boot server from `backend/` via `python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000`; verify:
  - `GET /api/v1/auth/login` → 404 (router gone).
  - `GET /api/v1/chat/…` with no token → 200.
- Grep `flutter_app/lib/` for stray auth/token references; confirm none (Flutter has no web auth integration expected).
- Push to git (`origin` = `github.com/Minaty001/Hinata`).

## Out of scope

- Telegram bot user handling (untouched).
- Dropping `Account`/`UserSession`/`Identity` tables.
- Re-introducing registration/login in any form.

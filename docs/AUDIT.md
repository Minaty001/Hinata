# Hinata — Complete Repository Audit

> Generated: 2026-08-09  
> Auditor: Antigravity AI Architect

---

## 1. Architecture Overview

### 1.1 Current Backend Architecture

The backend is a **custom Python HTTP server** (`app.py`) built on Python's standard library
`http.server.HTTPServer` / `SimpleHTTPRequestHandler`. There is **no FastAPI, no ASGI,
no WebSocket, no authentication, no authorization**.

- Entry point: `app.py` — serves static files from `web/` AND handles REST API routes
- Custom routing: manual `if self.path.startswith("/api/...")`
- Async simulation: `asyncio.new_event_loop()` + `loop.run_until_complete()` per request (blocking)
- No middleware, no JWT, no sessions
- Database: SQLite via a custom `AsyncSessionWrapper` wrapping `sqlite3` through `asyncio.to_thread()`

**Telegram bot** (`bot.py`) is a separate process using `python-telegram-bot` v20.

Both processes share the same SQLite database file but run independently with no shared runtime.

### 1.2 Current Frontend Architecture

The web frontend is a **monolithic single-page application** (`web/index.html`, `web/app.js`, `web/style.css`):
- Pure vanilla HTML/CSS/JS, no framework
- ~47 KB of JavaScript in a single file
- Chat UI, memory viewer, search, provider settings — all inline
- PWA manifest + service worker present
- APK files were committed directly to `web/` (removed in Phase 0)

### 1.3 Current Android Architecture

The Android app (`flutter_app/`) is a **Flutter WebView wrapper**:
- Splash screen → immediately loads `WebViewApp`
- `WebViewApp` embeds the entire web UI via `WebViewController`
- URLs now configurable via SharedPreferences (fixed in Phase 0; were hardcoded `10.0.2.2:8000`)
- **No native Kotlin code**
- **No MethodChannels**
- **No device control (Accessibility, MediaControl, etc.)**
- **No offline capability**
- **No voice features**

### 1.4 Current Telegram Architecture

- Separate process: `bot.py` + `handlers/` directory
- Uses `python-telegram-bot` v20
- Full AI pipeline in `handlers/message_handler.py` (556 lines, 16-step pipeline)
- **Duplicates the AI pipeline** from `app.py` — same engines, separate instances, no shared brain

### 1.5 Current Database Architecture

**ORM**: SQLAlchemy 2.0 (sync engine, wrapped in `AsyncSessionWrapper`)  
**Database**: SQLite (`data/hinata.db`)  
**No migrations** (Alembic not configured — `create_all()` at startup)

Tables:
| Table | Purpose |
|-------|---------|
| `users` | Telegram-centric user profile + mood + relationship_score + personality |
| `chains` | Conversation threads |
| `conversations` | Individual messages |
| `memories` | Key-value fact/preference/goal storage |
| `preferences` | Per-user settings |
| `settings` | Global bot settings (active_provider, API keys) |
| `session_indices` | Topic index per chain for search |
| `feeling_snapshots` | Emotion vectors per message |
| `training_samples` | Encoded interaction JSON |
| `relationship_dimensions` | Multi-dimensional trust/intimacy scores |

### 1.6 Current AI Architecture

**Provider client**: `ai/unified_ai_client.py` — supports 6 providers:
Groq, OpenCode Zen, OpenAI, Gemini, OpenRouter, Bytez

**AI Engines (all rule-based, no ML)**:
- `feeling_detector`, `need_analyzer`, `defense_detector`, `response_mode_selector` (8 modes),
  `mood_engine`, `personality_engine` (8 types), `relationship_engine`, `prompt_builder`,
  `context_builder`, `distress_detector`, `vulnerability_scaffold`, `response_cleaner`, `language_detector`

**Training module** (`training/`): Behavioral tracker, quality scorer, conversation encoder, model router.
The name `training` is misleading — this is **behavioral analysis and interaction logging**, not model training.

### 1.7 Current Memory System

`memory/memory_manager.py` — simple CRUD:
- **No semantic search**, **no embeddings**, **no retrieval ranking**
- All memories loaded in full every prompt (no context budget)

### 1.8 Current Deployment

- `start.sh` — manual startup script
- No Dockerfile, no docker-compose.yml, no render.yaml
- Designed for Termux/Android Linux as primary target

---

## 2. Feature Inventory

| Feature | Classification | Notes |
|---------|---------------|-------|
| Telegram bot text chat | **KEEP** | Working |
| Telegram commands | **KEEP** | Functional |
| Admin command | **KEEP** | Owner-gated |
| Multi-provider AI (6 providers) | **KEEP** | Good abstraction |
| Provider fallback | **KEEP** | Automatic |
| Web chat UI | **KEEP/REFACTOR** | Functional but monolithic |
| Conversation chains/sessions | **KEEP** | Good threading model |
| Session topic index | **KEEP** | Useful for search |
| Memory system (basic) | **REFACTOR** | Too simplistic |
| Feeling/emotion detection | **KEEP** | Well-implemented |
| Distress detection + CARE protocol | **KEEP** | Important safety feature |
| Response mode selection (8 modes) | **KEEP** | Emotional intelligence |
| Personality system (8 types) | **KEEP** | Works |
| Mood engine | **KEEP** | Works |
| Relationship engine | **REFACTOR** | Message-length scoring is poor |
| Multi-language support (Hinglish) | **KEEP** | Core feature |
| Rate limiting | **KEEP** | Needs auth integration |
| Maintenance mode | **KEEP** | Admin feature |
| SQLite database | **REFACTOR** | Needs PostgreSQL for production |
| Android WebView app | **REPLACE** | Must become native-first Flutter |
| Android hard-coded URLs | **FIXED** | Fixed in Phase 0 |
| Keystore in repository | **FIXED** | Removed in Phase 0 |
| API keys stored in DB plaintext | **REFACTOR** | Phase 1 |
| CORS wildcard (*) | **FIXED** | Fixed in Phase 0 |
| Hardcoded web user ID | **FIXED** | Replaced with shim in Phase 0 |
| APK binaries in web/ | **FIXED** | Removed in Phase 0 |
| Authentication/authorization | **MISSING** | Phase 1 |
| JWT | **MISSING** | Phase 1 |
| WebSocket | **MISSING** | Phase 1 |
| FastAPI | **MISSING** | Phase 1 |
| Device control | **MISSING** | Phase 6 |
| Voice (STT/TTS) | **MISSING** | Phase 9 |
| Offline mode | **MISSING** | Phase 11 |
| Goal/task system | **MISSING** | Phase 10 |
| Agent runtime | **MISSING** | Phase 4 |
| Reflex Brain | **MISSING** | Phase 3 |
| Semantic memory + embeddings | **MISSING** | Phase 5 |
| Alembic migrations | **MISSING** | Phase 1 |
| Docker | **MISSING** | Phase 12 |

---

## 3. Security Audit Results

### Issues Fixed in Phase 0

| Issue | Location | Fix |
|-------|----------|-----|
| Keystore file in repo | `flutter_app/android/keystore/hinata-keystore.jks` | Removed from git tracking; `.gitignore` updated |
| Hardcoded password `hinata123` | `flutter_app/android/app/build.gradle:51-53` | Removed; CI env vars required |
| Wildcard CORS `*` | `app.py:194`, `app.py:648` | Replaced with `_WEB_ORIGINS` allowlist |
| Hardcoded web user ID 999999 | `services/user_service.py:69` | Replaced with migration shim + deprecation warning |
| Android emulator URL `10.0.2.2` | `flutter_app/lib/main.dart:115-116` | Now loaded from SharedPreferences |
| APK binaries in repo | `web/hinata-android*.apk` | Removed from git tracking |
| `.gitignore` missing keystore patterns | `.gitignore` | Added `*.jks`, `*.keystore`, `*.apk`, etc. |
| `.env.example` missing security vars | `.env.example` | Added JWT_SECRET, WEB_ORIGINS, signing docs |

### Issues Remaining (to be fixed in subsequent phases)

| Issue | Target Phase |
|-------|-------------|
| No authentication on any API endpoint | Phase 1 |
| API keys stored in DB plaintext | Phase 1 |
| No input validation on web API | Phase 1 |
| No rate limiting on web API | Phase 1 |
| Duplicate AI brain (no shared core) | Phase 2 |
| No HTTPS/TLS | Phase 12 |

> [!CAUTION]
> The original keystore (`hinata-keystore.jks`) was publicly exposed with password `hinata123`.
> **It must be considered compromised.** Any APKs signed with it should be superseded by
> new APKs signed with a fresh keystore. Generate a new keystore before making any release builds.

---

## 4. Android Audit

| Item | Status |
|------|--------|
| Implementation | WebView wrapper — not a native app |
| MethodChannels | None |
| Native Kotlin code | None |
| AccessibilityService | Not implemented |
| MediaController | Not implemented |
| VoiceController | Not implemented |
| Offline capability | None |
| Hard-coded URLs | FIXED (Phase 0) |
| Keystore in repo | FIXED (Phase 0) |
| Hardcoded password | FIXED (Phase 0) |
| Min SDK | 28 (Android 9) |
| Target SDK | 35 |

---

## 5. AI Audit

| Item | Status |
|------|--------|
| Provider abstraction | GOOD — UnifiedAIClient wraps 6 providers |
| Model routing | PARTIAL — routes by response mode, not task type |
| Prompt system | GOOD — layered PromptBuilder |
| Memory retrieval | POOR — all memories loaded in full, no ranking |
| Personality | GOOD — 8 personalities, cleanly separated |
| Context building | BASIC — returns last N messages only |
| Fallback handling | GOOD — automatic provider fallback |
| Streaming | NOT IMPLEMENTED |
| Feeling detection | GOOD — rule-based, no LLM dependency |
| Distress/crisis detection | GOOD — CARE protocol present |
| Training module | MISLEADING NAME — rename to behavioral_analysis |

---

## 6. Testing Audit

| Test File | Coverage |
|-----------|---------|
| `tests/test_app.py` | Basic HTTP routing only |
| `tests/test_multi_provider.py` | Provider switching |
| `tests/test_session_indexing_hinglish.py` | Session index creation |
| `tests/test_storage_chains.py` | Chain CRUD |

**Missing**: auth, authorization, security, agent, memory retrieval, WebSocket, Android,
Telegram, voice, device pairing, permission enforcement, prompt injection, cross-user isolation.

---

## 7. Phase Completion Tracker

| Phase | Status | Notes |
|-------|--------|-------|
| 0 — Security Cleanup | ✅ COMPLETE | All 8 critical issues resolved |
| 1 — FastAPI Backend | ⏳ PENDING | |
| 2 — Unified Identity + Brain | ⏳ PENDING | |
| 3 — Reflex Brain | ⏳ PENDING | |
| 4 — Agent/Tool Runtime | ⏳ PENDING | |
| 5 — Memory 2.0 | ⏳ PENDING | |
| 6 — Android Device Agent | ⏳ PENDING | |
| 7 — Web Frontend | ⏳ PENDING | |
| 8 — Telegram Thin Client | ⏳ PENDING | |
| 9 — Voice | ⏳ PENDING | |
| 10 — Events/Tasks/Goals | ⏳ PENDING | |
| 11 — Offline Mode | ⏳ PENDING | |
| 12 — Production Hardening | ⏳ PENDING | |

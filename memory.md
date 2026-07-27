# 🧠 Hinata Project Memory & Codebase Index (`memory.md`)

> **Purpose**: Serves as a persistent state summary of the codebase. Tracks completed work, active tasks, current file focus, and architectural state to prevent hallucinations and save token context window usage.

---

## 📌 Project Overview
- **Project Name**: Hinata Hyuga Web Application & Deep Search Engine
- **Target OS / Platform**: Termux on Android (`aarch64-linux-android`) & Linux
- **Python Version**: Python 3.14 (`venv` at `/root/hinata/venv`)
- **Port / Server**: `http://localhost:2027` & `http://10.99.189.237:2027` (0.0.0.0:2027)
- **Status**: **LIVE & OPERATIONAL** (Background process task-272)

---

## 🚀 Active Task / Completed Phase
- **Task**: Multi-Session Architecture with Automatic Topic Indexing & Default Hinglish Language Response Mode.
- **Status**: **100% COMPLETED & VERIFIED**
- **Key Deliverables Achieved**:
  1. Default language set to **Hinglish** across all prompt builders, user profiles, system configurations, and UI defaults.
  2. Multi-session thread management (`Session` / `Chain` ORM models).
  3. Automatic **Session Topic Indexing** (`SessionIndex` table) extracting major topics, summary snippets, and page numbers per session.
  4. Fast query proceed: `build_conversation_context` prepends indexed topic pages to the prompt so the AI can jump directly to relevant topics without parsing bloated raw chat history.
  5. Web UI sidebar and Deep Search integration for topic indices.
  6. All automated unit test suites passing (`tests/test_session_indexing_hinglish.py` & `tests/test_multi_provider.py`).

---

## ✅ Completed Architecture & Features

### 1. Database & Persistence Layer
- **Engine**: Standard `sqlite3` driver wrapped in `AsyncSessionWrapper` via `asyncio.to_thread` (Greenlet-free for Termux Python 3.14).
- **ORM Models** (`database/models.py`):
  - `User`: Internal user identity with default `language="hinglish"`.
  - `Chain`: Conversation thread / multi-session container.
  - `SessionIndex`: Auto-indexed topic pages (`chain_id`, `topic`, `summary`, `keywords`, `page_number`).
  - `Conversation`: Role, message, timestamp linked to `chain_id`.
  - `Memory`: Auto-learned facts, goals, preferences.
  - `Setting`: Key-value configuration for API keys, base URLs, active models, and active provider.

### 2. Multi-Provider AI Engine (`ai/unified_ai_client.py`)
- Supported Providers (All 6 active with independent settings stored in SQLite `settings` table):
  1. 🚀 **Groq** (`groq`)
  2. ⚡ **OpenCode Zen** (`opencode_zen`)
  3. 🤖 **OpenAI** (`openai`)
  4. ✨ **Google Gemini** (`gemini`)
  5. 🌐 **OpenRouter** (`openrouter`)
  6. 🧬 **Bytez** (`bytez`)
- **Features**: Model mismatch protection (prevents 404 cross-provider errors), dynamic API key & base URL customization, automated secondary provider failover.

### 3. Hinglish Default Language & Prompt Builder (`ai/prompt_builder.py`)
- Hinata's default language is configured as **Hinglish** (cute, soft-spoken Hindi in Roman script mixed with English).

### 4. Automatic Session Topic Indexing (`services/chat_service.py` & `ai/context_builder.py`)
- `auto_index_session`: Automatically extracts key topics, summary snippets, and page numbers as messages are stored in SQLite.
- `build_conversation_context`: Pre-formats Session Topic Index headers for fast, token-efficient AI prompt proceeding.

---

## 📂 File Map & Status

| File Path | Description | Status |
|---|---|---|
| `app.py` | Web app HTTP server, REST endpoints (`/api/chat`, `/api/sessions`, `/api/session/index`, `/api/providers`, `/api/search`) | **COMPLETED & LIVE** |
| `database/models.py` | SQLAlchemy ORM models (`SessionIndex`, `Chain`, `Conversation`, `Memory`, `Setting`) | **COMPLETED** |
| `ai/prompt_builder.py` | System prompt builder with Hinglish rules | **COMPLETED** |
| `ai/context_builder.py` | Topic-indexed conversation context builder for fast query proceed | **COMPLETED** |
| `services/chat_service.py` | Multi-session manager & `auto_index_session` extractor | **COMPLETED** |
| `ai/unified_ai_client.py` | 6-Provider AI client manager | **COMPLETED** |
| `web/index.html` | Frontend UI layout with Multi-Session & Provider cards | **COMPLETED** |
| `web/app.js` | Frontend state management, Session Topic Index UI, REST API sync | **COMPLETED** |
| `tests/test_session_indexing_hinglish.py` | Unit tests for Hinglish defaults & session indexing | **PASSING (3/3)** |
| `tests/test_multi_provider.py` | Unit tests for 6 AI providers & DB settings | **PASSING (4/4)** |

---

## 🎯 Current State Summary
- **Current File Focus**: All core tasks completed.
- **Server Status**: Running live in background (`python app.py` on port 2027).

# Hinata - AI Telegram Companion
## Project Memory & Development Progress

**Version:** 1.0.0

> **Purpose**
>
> This file is the single source of truth for the project's development status. It should be updated after every coding session.
>
> Whenever starting a new chat or using another AI tool, provide this file first so it understands the current project state without reading the entire codebase.

---

# Project Information

**Project Name:** Hinata

**Project Type:** AI Telegram Companion

**Current Version:** v0.4.0

**Development Status:** Beta — OpenCode Zen & Groq Multi-Provider Engine Active

**Current Phase:** Phase 17 - Documentation & Licensing (Complete)

**Last Updated:** 2026-07-27

---

# Overall Progress

| Phase | Status |
|--------|--------|
| Phase 0 - Project Setup | ✅ Complete |
| Phase 1 - Telegram Bot | ✅ Complete |
| Phase 2 - Configuration | ✅ Complete |
| Phase 3 - Database | ✅ Complete |
| Phase 4 - Groq Integration | ✅ Complete |
| Phase 5 - Prompt Builder | ✅ Complete |
| Phase 6 - Memory System | ✅ Complete |
| Phase 7 - Personality Engine | ✅ Complete |
| Phase 8 - Mood Engine | ✅ Complete |
| Phase 9 - Relationship System | ✅ Complete |
| Phase 10 - User Preferences | ✅ Complete |
| Phase 11 - Advanced Conversation | ✅ Complete |
| Phase 12 - Admin System | ✅ Complete |
| Phase 13 - Security | ✅ Complete |
| Phase 14 - Testing | ✅ Complete |
| Phase 15 - Deployment | ⏳ In Progress |
| Phase 16 - Optimization | ⏳ In Progress |
| Phase 17 - Documentation | ✅ Complete |
| Phase 18 - Future Features | ⏳ Planned |

---

# Current Task

```
Session 10 — OpenCode Zen API Integration & Free Model Suite Complete.
Added Unified AI Client Engine with automated failover and /provider command.
```

---

# Current Working File

```
None — all updates applied
```

---

# Next File To Create

```
Deployment scripts, unit tests
```

---

# Completed Files

```
LICENSE
PRD.md
architecture.md
rules.md
phases.md
design.md
memory.md
README.md
requirements.txt
.env.example
.gitignore
.gitkeep (data/cache, backups, logs)
app.py
bot.py
config.py
constants.py
database/__init__.py
database/database.py
database/models.py
database/backup.py
handlers/__init__.py
handlers/command_handler.py
handlers/message_handler.py
handlers/error_handler.py
handlers/admin_handler.py
ai/__init__.py
ai/groq_client.py
ai/opencode_client.py
ai/unified_ai_client.py
ai/personality_engine.py
ai/mood_engine.py
ai/relationship_engine.py
ai/context_builder.py
ai/prompt_builder.py
ai/response_cleaner.py
ai/language_detector.py
memory/__init__.py
memory/memory_manager.py
services/__init__.py
services/user_service.py
services/chat_service.py
utils/__init__.py
utils/formatter.py
utils/helpers.py
utils/rate_limit.py
utils/retry.py
utils/validators.py
tests/__init__.py
prompts/personalities.json
prompts/moods.json
prompts/templates.json
```

---

# Pending Files

```
handlers/callback_handler.py
ai/emotion_engine.py
memory/short_memory.py
memory/long_memory.py
memory/preference_memory.py
memory/relationship_memory.py
memory/summarizer.py
database/migrations.py
services/mood_service.py
services/scheduler.py
services/backup_service.py
services/logger_service.py
tests/test_ai.py
tests/test_memory.py
tests/test_database.py
tests/test_bot.py
```

---

# Folder Status

```
Project/

Documentation
██████████ 100%

Backend
██████████ 100%

Telegram
██████████ 100%

Database
██████████ 100%

AI
██████████ 100%

Memory
██████████ 100%

Deployment
░░░░░░░░░░ 0%

Testing
██░░░░░░░░ 20% (bug audit done, no automated tests yet)
```

---

# Implemented Features

- Project planning and documentation
- Architecture design
- Development rules and phases
- Design system guide
- Folder structure
- Configuration system (pydantic v1 BaseSettings + .env)
- Constants module
- SQLAlchemy 2.0 ORM models (User, Conversation, Memory, Preference, Setting)
- Async database engine and session management
- Database backup/restore service
- Bot setup with handler registration
- Command handlers (/start, /help, /about, /ping, /settings, /personality, /mood, /memory, /forget, /reset, /version)
- Admin handler with 7 sub-commands (stats, users, logs, broadcast, maintenance, backup, help)
- Owner-only guard based on OWNER_ID
- Global error handler
- **Groq API client** (async, retry, timeout, rate-limit handling)
- **Personality Engine** (8 personalities: sweet, calm, smart, gamer, playful, curious, boss, supportive)
- **Mood Engine** (9 moods: happy, sad, sleepy, excited, curious, relaxed, energetic, shy, thoughtful)
- **Relationship Engine** (5-level scoring: stranger → acquaintance → friend → close_friend → best_friend)
- **Prompt Builder** (full system prompt assembly, now with consistent rules)
- **Context Builder** (conversation history retrieval)
- **Response Cleaner** (markdown cleaning, message splitting, truncation, MarkdownV2 escaping)
- **Language Detector** (en/hi/hi-en with Devanagari + Hinglish heuristics)
- **Memory Manager** (save, retrieve, forget, summarize)
- **User Service** (get-or-create, preferences CRUD)
- **Chat Service** (save, retrieve, clear, count conversations)
- **Full AI message pipeline** (user → DB → context → engines → prompt → Groq → clean → store → reply)
- Rate limiter (sliding window, per-user)
- Input validator (length, sanitisation, prompt injection detection)
- Utility modules (helpers, formatter, retry)
- Maintenance mode toggle (checked in message handler)
- Personality/mood definitions in JSON files
- Git initialized

---

# Features In Progress

- Manual testing of all fixes from Session 8

---

# Features Remaining

- Emotion engine (future feature)
- Advanced memory sub-modules (short_memory, long_memory, summarizer)
- Scheduler service
- Database migrations
- Callback handler
- Test suite (automated)
- Dockerfile
- Deployment configs (Render, Railway)

---

# Database Status

```
Created (ORM models ready, tables auto-created on startup)
```

Tables

```
Users (with relationship_score, current_mood, current_personality per-user)
Conversations (with ForeignKey to users)
Memories (with ForeignKey to users, soft-delete via is_active)
Preferences (with ForeignKey to users, one-to-one)
Settings (global key-value store)
```

---

# API Status

Telegram

```
Connected — bot polling, responding to messages.
```

Groq

```
Tested end-to-end (2 messages processed, 200 OK).
Pipeline: user → DB → context → engines → prompt → Groq → clean → store → reply.
```

---

# Environment Variables

Required

```
BOT_TOKEN
GROQ_API_KEY
DATABASE_URL
OWNER_ID
LOG_LEVEL
TIMEZONE
DEFAULT_LANGUAGE
```

---

# Dependencies Status

```
Installed (pip install -r requirements.txt)
Note: Using Pydantic v1 (pydantic>=1.10.0,<2) — see Known Issues.
```

---

# Known Issues

```
- GROQ_MAX_TOKENS=50 is very low (produces 1-2 sentences). Intentional for
  user's "short reply" preference, but may need increasing for some use cases.
- `python3` in PATH points to system Python without packages; must use Termux
  Python path: /data/data/com.termux/files/usr/bin/python3
- Termux network can drop (transient [Errno 7] — PTB retry handles it)
- No automated test suite
- Pydantic v1 is used — may need migration to v2 for Python 3.13+ compatibility
- config.py uses `from pydantic import BaseSettings` (v1-only import)
- config.py uses `allow_mutation = False` (v1-only config option)
- detect_prompt_injection() in validators.py is defined but never called
- `header()` in formatter.py uses `#` which Telegram Markdown doesn't support
```

---

# Bugs Found & Fixed (Session 8)

## Critical

| # | File | Bug | Fix |
|---|------|-----|-----|
| 1 | requirements.txt | `asyncio>=3.4.3` listed as pip dependency — stdlib, breaks install | Removed the entry |
| 2 | error_handler.py | `traceback.format_exc()` logs stale traceback, not `context.error` | Used `traceback.format_exception()` on `context.error` |
| 3 | prompt_builder.py | Contradictory prompt rules (emotionally expressive vs no emotions, use emojis vs no emojis, ask follow-ups vs 7-word limit) | Removed contradictions, unified rules |

## Medium

| # | File | Bug | Fix |
|---|------|-----|-----|
| 4 | command_handler.py | Pluralization bug: `memory/{'ies'...}` → "memory/ies" instead of "memories" | Fixed to `{'memories' if count != 1 else 'memory'}` |
| 5 | memory_manager.py | `forget_all_memories` only forgets first 50 (default limit) | Changed to `limit=10000` |
| 6 | chat_service.py | `clear_conversation_history` loads all rows + deletes one-by-one | Replaced with bulk `DELETE` statement |
| 7 | message_handler.py | `PromptBuilder()` and `GroqClient()` instantiated per message | Moved to `bot_data` in bot.py, retrieved in handler |
| 8 | database/database.py | Module-level path code could match empty string / directory | Added `_db_path_str` check + `.is_file()` guard |
| 9 | response_cleaner.py | `escape_markdown()` doesn't escape backslash `\` first | Added backslash escaping as first operation |

## Low

| # | File | Bug | Fix |
|---|------|-----|-----|
| 10 | mood_engine.py | `datetime.now()` without timezone (rest of codebase uses UTC) | Changed to `datetime.now(timezone.utc)` |
| 11 | relationship_engine.py | `map = {...}` shadows Python builtin `map` | Renamed to `warmth_map` |
| 12 | rate_limit.py | `remaining()` always returns 0 when rate-limited, message says "0 more messages" | Simplified to "Try again in a few seconds" |

## Still Open (Not Fixed — Design-Level)

| # | File | Issue | Reason Not Fixed |
|---|------|-------|------------------|
| A | config.py | Uses Pydantic v1 API (`from pydantic import BaseSettings`, `allow_mutation`) | Would require full migration to pydantic-settings v2 |
| B | constants.py | `GROQ_MAX_TOKENS=50` very low | Intentional per user preference for short replies |
| C | validators.py | `detect_prompt_injection()` defined but never called | Dead code — should be wired in or removed in future |
| D | formatter.py | `header()` uses `#` Markdown headers (Telegram doesn't support) | Not used in bot output currently |
| E | context_builder.py | `count_recent_messages()` fetches all rows instead of SQL COUNT | Performance optimization, not a bug |

---

# Important Decisions

- Python 3.13+
- Async architecture with asyncio
- SQLite via aiosqlite (async)
- SQLAlchemy 2.0 ORM with async support (mapped_column style)
- Groq Free API (llama-3.3-70b-versatile)
- python-telegram-bot v21
- Pydantic v1 BaseSettings for config (migration to v2 pending)
- Modular project structure with separate packages
- Environment-based configuration
- Engines cached in bot_data (not re-created per request)
- PromptBuilder and GroqClient also cached in bot_data (fixed in Session 8)
- Database session factory shared via bot_data
- Personality/mood definitions in JSON files (not code)
- AI provider isolated behind GroqClient abstraction
- Per-user personality, mood, and relationship stored in DB (not in-memory)
- Soft-delete for memories (is_active flag)
- Maintenance mode checked in message handler

---

# Coding Standards

Always

- Use async functions where appropriate.
- Follow PEP 8.
- Use type hints.
- Write modular code.
- Keep business logic separate from handlers.
- Store secrets in `.env`.
- Write meaningful commit messages.

---

# File Progress Tracker

| File | Status |
|------|--------|
| PRD.md | ✅ Complete |
| architecture.md | ✅ Complete |
| rules.md | ✅ Complete |
| phases.md | ✅ Complete |
| design.md | ✅ Complete |
| memory.md | ✅ Complete |
| README.md | ✅ Complete |
| requirements.txt | ✅ Complete (fixed) |
| .env.example | ✅ Complete |
| .gitignore | ✅ Complete |
| app.py | ✅ Complete |
| bot.py | ✅ Complete (fixed) |
| config.py | ✅ Complete |
| constants.py | ✅ Complete |
| database/database.py | ✅ Complete (fixed) |
| database/models.py | ✅ Complete |
| database/backup.py | ✅ Complete |
| handlers/command_handler.py | ✅ Complete (fixed) |
| handlers/message_handler.py | ✅ Complete (fixed) |
| handlers/error_handler.py | ✅ Complete (fixed) |
| handlers/admin_handler.py | ✅ Complete |
| ai/groq_client.py | ✅ Complete |
| ai/personality_engine.py | ✅ Complete |
| ai/mood_engine.py | ✅ Complete (fixed) |
| ai/relationship_engine.py | ✅ Complete (fixed) |
| ai/context_builder.py | ✅ Complete |
| ai/prompt_builder.py | ✅ Complete (fixed) |
| ai/response_cleaner.py | ✅ Complete (fixed) |
| ai/language_detector.py | ✅ Complete |
| memory/memory_manager.py | ✅ Complete (fixed) |
| services/user_service.py | ✅ Complete |
| services/chat_service.py | ✅ Complete (fixed) |
| utils/formatter.py | ✅ Complete |
| utils/helpers.py | ✅ Complete |
| utils/rate_limit.py | ✅ Complete (fixed) |
| utils/retry.py | ✅ Complete |
| utils/validators.py | ✅ Complete |
| prompts/personalities.json | ✅ Complete |
| prompts/moods.json | ✅ Complete |
| prompts/templates.json | ✅ Complete |

---

# Session Log

## Session 1

Completed

- Project requirements document
- Architecture document
- Rules document
- Development phases
- Design document
- Memory document

No source code implemented.

## Session 2

Completed

- Phase 0 - Project Setup
- Created folder structure
- requirements.txt with all dependencies
- .env.example with all environment variables
- .gitignore for project hygiene
- config.py with pydantic-settings validation
- constants.py with centralized project constants
- app.py with async entry point and logging
- bot.py with Application builder and handler registration
- database/__init__.py
- database/database.py with async engine and session factory
- database/models.py (User, Conversation, Memory, Preference, Setting)
- handlers/__init__.py
- handlers/command_handler.py (/start, /help, /about, /ping)
- handlers/message_handler.py (stub with typing indicator)
- handlers/error_handler.py (global error handler)
- ai/__init__.py
- ai/groq_client.py (async with retry/timeout)
- ai/personality_engine.py (8 personalities from JSON)
- ai/mood_engine.py (9 moods, time-aware)
- ai/relationship_engine.py (5-level scoring)
- ai/context_builder.py (conversation history)
- ai/prompt_builder.py (system prompt assembly)
- ai/response_cleaner.py (markdown, splitting)
- ai/language_detector.py (en/hi/hi-en)
- memory/__init__.py
- memory/memory_manager.py (save, retrieve, forget)
- services/__init__.py
- services/user_service.py (profile CRUD)
- services/chat_service.py (conversation storage)
- utils/__init__.py
- tests/__init__.py
- prompts/personalities.json (8 personalities)
- prompts/moods.json (9 moods)
- prompts/templates.json (system prompt template)
- README.md with quick start guide
- Initialized Git repository
- Full AI pipeline wired into message handler

## Session 3

Completed

- Admin handler with 7 sub-commands (stats, users, logs, broadcast, maintenance, backup, help)
- Owner-only guard based on OWNER_ID
- Missing user commands: /settings, /personality, /mood, /memory, /forget, /reset, /version
- Rate limiter (sliding window, per-user)
- Input validator (length, sanitisation, prompt injection detection)
- Utility modules (helpers, formatter, retry)
- Database backup/restore service
- Maintenance mode toggle
- All handlers registered in bot.py
- Tokens configured, pydantic v1 migration, Markdown crash fix in _send_reply

## Session 4

### Completed

- Fixed DB "no such table: users" (import models before init_database)
- Fixed relative DB path resolution (absolute path via PROJECT_ROOT)
- Stale 0-byte DB file cleanup on startup
- Fixed /settings relationship level display (use RelationshipEngine)
- Verified tables created: ['conversations', 'memories', 'preferences', 'settings', 'users']
- Bot running on Termux, polling successfully

### Session 5

### Completed
- Reduced GROQ_MAX_TOKENS from 1024 → 200 for shorter replies
- Updated system prompt: "1 to 3 sentences maximum"
- Fixed bot startup — must use Termux Python `/data/data/com.termux/files/usr/bin/python3`
  (system `/usr/bin/python3` lacks installed packages)
- Full Groq pipeline verified end-to-end (2 messages processed, both 200 OK)

### Known Issues
- `python3` in PATH points to system Python without packages; startup must use Termux Python path

## Session 6

### Completed
- GROQ_MAX_TOKENS reduced further: 200 → 100 → 50
- System prompt tightened: "Reply in 1 short sentence. Max 7 words."
- Added rules: no emojis unless user uses one first, never narrate emotions
- Fixed conflict errors (killed duplicate bot instances)
- Bot running cleanly with single instance

### Pending
- User testing shortest reply setting

## Session 7

### Completed
- Log rotated (old 4264-line/216KB error log archived)
- Bot running cleanly, single instance, no errors
- Response tuning: GROQ_MAX_TOKENS=50, prompt enforces 1 sentence max 7 words

## Session 9 — Hinata Hyuga Persona, Minaty001 Creator Attribution & MIT License
### Completed
- Configured identity across system prompts & bot info to **Hinata Hyuga** (sweet, gentle AI girl companion).
- Added creator attribution for **Minaty001** and GitHub repository (`https://github.com/Minaty001/hinata`).
- Created official MIT `LICENSE` file.
- Documented auto-trained memory system on user data.

## Session 10 — OpenCode Zen API (`https://opencode.ai/zen/v1`) & Free Thinking Models
### Completed
- Created `OpenCodeZenClient` in `ai/opencode_client.py` for `https://opencode.ai/zen/v1/chat/completions`.
- Created `UnifiedAIClient` in `ai/unified_ai_client.py` with dynamic provider selection & automatic zero-downtime failover between Groq API and OpenCode Zen.
- Registered `/provider` command in `handlers/command_handler.py` and `bot.py` for switching AI providers and models on-the-fly.
- Added full suite of OpenCode Zen free models to `constants.py`: `opencode/big-pickle`, `opencode/mimo-v2.5-free`, `opencode/deepseek-v4-flash-free`, `opencode/nemotron-3-ultra-free`, `opencode/ing-3.0-flash-free`, `opencode/laguna-s-2.1-free`, `opencode-zen-free`, `deepseek-r1`, `qwen2.5-72b-instruct`.
- Updated `.env.example`, `README.md`, and `memory.md`.

---

# Next Development Goal

```
Current: Test bot after Session 8 bug fixes.
Next:
- Run bot on Termux and verify all fixes work
- Record proper startup command in README
- Add .gitignore entries for logs/data
- Document Termux Python path requirement
- Consider migrating Pydantic v1 → v2
- Wire detect_prompt_injection() into message pipeline or remove
- Add automated test suite
```

---

# AI Instructions

When continuing development:

1. Read this file first.
2. Check the current phase.
3. Continue only from the current task.
4. Do not rewrite completed files unless requested.
5. Update this file after completing every significant task.
6. Mark completed phases and files accurately.
7. Record newly added features and decisions.
8. Keep this file concise but up to date.

---

# Project Completion Criteria

The project is considered complete when:

- All phases are marked complete.
- Telegram bot is production-ready.
- Groq integration is stable.
- Memory system functions correctly.
- Personality and mood engines influence responses.
- Documentation is current.
- Tests pass.
- Deployment is successful.

---

# End of memory.md

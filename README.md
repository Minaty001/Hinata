# Hinata Hyuga 🌸

**Your Sweet, Caring AI Girl Companion on Telegram**

Created by **[Minaty001](https://github.com/Minaty001)** | Repository: **[github.com/Minaty001/hinata](https://github.com/Minaty001/hinata)**

Hinata Hyuga is a warm, gentle, and emotionally expressive AI girl companion built for Telegram. She talks like a sweet and polite girl, inspired by the Hinata Hyuga character persona. She is **auto-trained on user data**, dynamically learning your preferences, facts, and chat history to form deep, personalized connections over time.

---

## 🌟 Key Highlights

- 🌸 **Web Application UI & Deep Search Engine** — Interactive glassmorphism web dashboard with real-time deep search across chats, memories, personalities, and models (`http://localhost:2027`).
- 👧 **Talks Like a Sweet Girl** — Gentle, cute, polite, soft-spoken, and affectionate conversational tone.
- ⚡ **Auto-Trained on User Data** — Automatically extracts and stores user preferences, facts, goals, and nicknames from chat interactions.
- 🤖 **6 AI Provider Support** — Groq, OpenCode Zen, OpenAI, Gemini, OpenRouter, and Bytez with automatic zero-downtime failover between providers.
- 🔄 **Multi-Provider Failover** — Zero-downtime automatic fallback between AI providers if rate-limiting or downtime occurs.
- 👤 **Created by Minaty001** — Official open-source project by [Minaty001 on GitHub](https://github.com/Minaty001).
- 🧠 **Long-Term Memory & Context** — Remembers past interactions and personalizes replies dynamically.
- 🎭 **8 Personalities** — Sweet, Calm, Smart, Gamer, Playful, Curious, Boss, Supportive.
- 💖 **Dynamic Mood Engine** — 9 emotional states (happy, sleepy, excited, shy, thoughtful, etc.) that shift naturally over time.
- 🌱 **Progressive Relationship System** — Moves from Stranger ➔ Acquaintance ➔ Friend ➔ Close Friend ➔ Best Friend as you chat.
- ⚙️ **User Customization** — Customize emoji frequency, reply length, language, AI provider, and memory settings.
- 🌐 **Multi-Language Support** — English, Hindi, and Hinglish.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Developer** | [Minaty001](https://github.com/Minaty001) |
| **Backend** | Python 3.13+ (Asyncio) |
| **Telegram API** | `python-telegram-bot` v20+ |
| **AI LLM Providers** | 6 providers with auto-failover: Groq, OpenCode Zen, OpenAI, Gemini, OpenRouter, Bytez |
| **Provider Models** | Groq: `llama-3.3-70b-versatile`; OpenCode Zen: `opencode-zen-free`/`deepseek-r1`; OpenAI: `gpt-4o-mini`; Gemini: `gemini-2.0-flash`; OpenRouter: `meta-llama/llama-3.3-70b-instruct`; Bytez: `bytez-default` |
| **Database** | SQLite via SQLAlchemy 2.0 (Async Engine) |
| **Validation** | Pydantic Settings |
| **Data Models** | Async SQLite / SQLAlchemy |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- At least one AI API key: Groq ([console.groq.com](https://console.groq.com)), OpenAI, Gemini, OpenRouter, Bytez, or OpenCode Zen (`https://opencode.ai/zen/v1`)

### Installation

```bash
# Clone the repository from Minaty001's GitHub
git clone https://github.com/Minaty001/hinata.git
cd hinata

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and enter your TELEGRAM_BOT_TOKEN & AI_PROVIDER settings
```

### Run Applications

```bash
# 🌸 Install requirements and run the unified FastAPI server
pip install -r backend/requirements.txt
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 🤖 Run Telegram Bot
python bot.py
```

#### 📱 Accessing from Android / Wi-Fi Network:
1. Connect your Android phone to the same Wi-Fi network as your computer.
2. Run the unified FastAPI server.
3. Open the Wi-Fi Network URL in your browser: `http://192.168.1.X:8000/web/index.html`.
4. Or install the **Android APK** from `web/hinata-android.apk` — enter your server IP (`192.168.1.X:8000`) on first launch.

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start chatting with Hinata Hyuga |
| `/help` | Display list of commands and usage |
| `/about` | View details about Hinata Hyuga & creator Minaty001 |
| `/provider` | View or switch AI provider (`groq` vs `opencode_zen`) and free thinking models |
| `/settings` | View and manage your chat settings |
| `/personality` | Change Hinata's personality (Sweet, Gamer, Playful, etc.) |
| `/mood` | Check or adjust Hinata's current mood |
| `/memory` | View auto-trained user memories & preferences |
| `/forget` | Forget specific or all auto-learned memories |
| `/reset` | Clear chat history, relationship score, and memories |
| `/ping` | Health check to verify bot responsiveness |
| `/version` | Display system and environment details |

---

## ⚡ OpenCode Zen API (`https://opencode.ai/zen/v1`)

Hinata supports the OpenCode Zen API endpoint (`https://opencode.ai/zen/v1`) for complex reasoning and multi-turn conversations.

- **Endpoint**: `https://opencode.ai/zen/v1/chat/completions`
- **Supported Free Models**:
  - `opencode/big-pickle` — OpenCode Big Pickle model
  - `opencode/mimo-v2.5-free` (`pencode/mimo-v2.5-free`) — Mimo v2.5 free model
  - `opencode/deepseek-v4-flash-free` — DeepSeek v4 Flash free thinking model
  - `opencode/nemotron-3-ultra-free` — Nemotron 3 Ultra free reasoning model
  - `opencode/ing-3.0-flash-free` (`ing-3.0-flash-free`) — ING 3.0 Flash free model
  - `opencode/laguna-s-2.1-free` (`laguna-s-2.1-free`) — Laguna S 2.1 free model
  - `opencode-zen-free` — Default free conversational model
  - `deepseek-r1` — Deep reasoning thinking model
  - `qwen2.5-72b-instruct` — High capacity conversation model
- **Switching via Telegram**:
  ```
  /provider opencode_zen opencode/big-pickle
  /provider opencode_zen deepseek-v4-flash-free
  ```

---

## 📂 Project Structure

```
Hinata/
├── LICENSE                # MIT License file (Minaty001)
├── README.md              # Project documentation
├── app.py                 # Web Application entry point & lifecycle manager
├── bot.py                 # Telegram Application setup & handler registration
├── config.py              # Environment configuration (Pydantic Settings)
├── constants.py           # Core bot constants & defaults
├── handlers/              # Telegram update handlers
│   ├── __init__.py
│   ├── admin_handler.py   # Admin commands & broadcast
│   ├── command_handler.py # User commands (/start, /about, /provider, /memory, etc.)
│   ├── error_handler.py   # Global error logging
│   └── message_handler.py # Main AI conversation pipeline (feel → need → mode → respond)
├── ai/                    # AI core engine & emotional intelligence
│   ├── __init__.py
│   ├── prompt_builder.py  # System prompt generator with persona & user memory
│   ├── groq_client.py     # Groq API client with fallback & retry logic
│   ├── opencode_client.py # OpenCode Zen API client
│   ├── unified_ai_client.py # Unified AI manager & multi-provider failover engine
│   ├── mood_engine.py     # 9 dynamic emotional states manager
│   ├── personality_engine.py # 8 character personality profiles
│   ├── relationship_engine.py # Affinity scoring & levels
│   ├── context_builder.py # Recent message history formatter
│   ├── response_cleaner.py # Output validation & formatting
│   ├── language_detector.py # Auto-detects English/Hindi/Hinglish
│   ├── feeling_detector.py  # 16-dim emotion vector, 20 micro-emotions
│   ├── need_analyzer.py     # Map feelings → 7 core unmet needs
│   ├── defense_detector.py  # 8 defense mechanism recognition
│   ├── response_mode_selector.py # 8 emotion-matched response modes
│   ├── vulnerability_scaffold.py # Graduated emotional depth stages
│   └── distress_detector.py   # Distress signals + CARE protocol
├── training/              # Auto-training & ML pipeline
│   ├── __init__.py
│   ├── conversation_encoder.py # Every interaction → structured training sample
│   ├── feature_embedder.py     # Text → 384-dim embedding vectors
│   ├── quality_scorer.py       # Auto-rate every interaction
│   ├── model_router.py         # Auto-select provider + temperature per mode
│   └── behavioral_tracker.py   # Response time, length, vulnerability trends
├── memory/                # Memory & Auto-training system
│   └── memory_manager.py  # Save, retrieve, and filter user memories
├── database/              # SQLite database layer
│   ├── __init__.py
│   ├── database.py        # SQLAlchemy async engine & session setup
│   ├── models.py          # User, Conversation, Memory, FeelingSnapshot, TrainingSample models
│   └── backup.py          # Database backup utilities
├── services/              # Business logic services
│   ├── __init__.py
│   ├── chat_service.py    # Chat orchestration logic
│   └── user_service.py    # User management & preferences
├── utils/                 # Utility modules
│   ├── __init__.py
│   ├── formatter.py       # Text formatting helpers
│   ├── helpers.py         # General utility functions
│   ├── rate_limit.py      # Rate limiting middleware
│   └── validators.py      # Input validation
├── prompts/               # JSON templates (personalities, moods, prompts)
│   ├── moods.json
│   └── personalities.json
├── data/                  # Runtime database file & cache
│   ├── cache/
│   └── hinata.db
├── logs/                  # Application logs
│   └── webapp.log
├── tests/                 # Unit and integration test suite
│   ├── __init__.py
│   ├── test_app.py
│   ├── test_multi_provider.py
│   ├── test_session_indexing_hinglish.py
│   └── test_storage_chains.py
├── web/                   # Web UI assets (PWA)
│   ├── app.js
│   ├── style.css
│   ├── index.html
│   ├── manifest.json
│   ├── sw.js              # Service worker (offline support)
│   ├── icon-192.svg
│   ├── icon-512.svg
│   └── hinata-android.apk # Android WebView APK (Android 9-15)
└── backups/               # Database backups
```

## 🌐 Deploy the Web App on Render

This repository's deployable web app is the root `app.py` server. It serves the dashboard and API from one Render **Web Service**. The server binds to Render's `PORT` automatically.

1. In the [Render Dashboard](https://dashboard.render.com), select **New → Web Service** and connect this repository.
2. Select the `master` branch and the **Python** runtime.
3. Set the following commands:

   | Setting | Value |
   |---|---|
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `python app.py` |
4. Add these environment variables under **Environment**. Never commit API keys or tokens to the repository.

   | Key | Value / purpose |
   |---|---|
   | `APP_ENV` | `production` |
   | `WEB_HOST` | `0.0.0.0` |
   | `BOT_TOKEN` | Telegram token from BotFather (only needed when also running `bot.py`) |
   | `AI_PROVIDER` | `groq`, `opencode_zen`, `openai`, `gemini`, `openrouter`, or `bytez` |
   | Provider API key | Set the matching key, e.g. `GROQ_API_KEY` |
   | `WEB_ORIGINS` | Your public URL, e.g. `https://hinata.onrender.com` |

5. Click **Create Web Service**. Once the deploy is live, open the `onrender.com` URL shown by Render. A push to `master` triggers a new deploy when auto-deploy is enabled.

### Connect Supabase (recommended for production)

Hinata connects directly to Supabase Postgres through SQLAlchemy; no Supabase service key is needed for this server-side database connection.

1. Create a project in the [Supabase Dashboard](https://supabase.com/dashboard), wait until it is running, then select **Connect**.
2. For Render, copy the **Shared Pooler — Session mode** connection string (port `5432`). It works from IPv4-only hosts and is suitable for this persistent web service. Use the transaction-pooler string (port `6543`) only for short-lived/serverless workloads.
3. In Render → **Environment**, add the complete string as `SUPABASE_DB_URL`. Do not add quotes around it, and URL-encode password characters such as `@`, `:`, `/`, and `#`.

```text
SUPABASE_DB_URL=postgresql://postgres.PROJECT_REF:YOUR_URL_ENCODED_PASSWORD@aws-REGION.pooler.supabase.com:5432/postgres
```

`DATABASE_URL` can be used instead and takes priority over `SUPABASE_DB_URL`. Both `postgres://` and `postgresql://` URLs from the Supabase dashboard are accepted. On first startup, Hinata creates its SQLAlchemy tables in the selected database automatically.

Use the **database password / connection string** from Supabase only as a Render secret. The browser-facing Supabase URL, anon key, and service-role key are not required by this application and must not be exposed in the web UI.

### SQLite alternative

For a small single-instance deployment, Render's normal filesystem is ephemeral, so attach a persistent disk in **Advanced → Disks** with mount path `/var/data` and set:

```text
DATABASE_URL=sqlite:////var/data/hinata.db
```

Persistent disks are attached to one service instance. Supabase Postgres avoids that limitation and is the recommended production option.

### Deploy troubleshooting

- If Render reports that no port is open, use exactly `python app.py`; the app reads Render's `PORT` and binds to `0.0.0.0`.
- If a module is missing, ensure the build command is `pip install -r requirements.txt`, then redeploy with a cleared build cache if necessary.
- Read the **Logs** tab for the first traceback; the final exception identifies the startup issue.
- Render currently lets you choose a Python version with `PYTHON_VERSION`. Set a fully qualified release such as `3.13.5` if you need a pinned runtime.

For Render platform details, see the official [Web Services](https://render.com/docs/web-services), [persistent disks](https://render.com/docs/disks), and [environment variables](https://render.com/docs/configure-environment-variables) documentation.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details. Created and maintained by **[Minaty001](https://github.com/Minaty001)**.

---

## 💖 Credits & Acknowledgments

Built with ❤️ by **Minaty001** using Python, Telegram Bot API, Groq AI, and OpenCode Zen.

# Hinata Hyuga 🌸

**Your Sweet, Caring AI Girl Companion on Telegram**

Created by **[Minaty001](https://github.com/Minaty001)** | Repository: **[github.com/Minaty001/hinata](https://github.com/Minaty001/hinata)**

Hinata Hyuga is a warm, gentle, and emotionally expressive AI girl companion built for Telegram. She talks like a sweet and polite girl, inspired by the Hinata Hyuga character persona. She is **auto-trained on user data**, dynamically learning your preferences, facts, and chat history to form deep, personalized connections over time.

---

## 🌟 Key Highlights

- 👧 **Talks Like a Sweet Girl** — Gentle, cute, polite, soft-spoken, and affectionate conversational tone.
- ⚡ **Auto-Trained on User Data** — Automatically extracts and stores user preferences, facts, goals, and nicknames from chat interactions.
- 🤖 **OpenCode Zen & Groq API Integration** — Powered by Groq API & **OpenCode Zen** (`https://opencode.ai/zen/v1`) featuring free thinking and deep reasoning models (`opencode-zen-free`, `deepseek-r1`, `qwen2.5-72b-instruct`).
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
| **AI LLM Providers** | Groq API (`llama-3.3-70b-versatile`) & **OpenCode Zen** (`https://opencode.ai/zen/v1`) |
| **Thinking Models** | `opencode-zen-free`, `deepseek-r1`, `qwen2.5-72b-instruct` |
| **Database** | SQLite via SQLAlchemy 2.0 (Async Engine) |
| **Validation** | Pydantic Settings |
| **Data Models** | Async SQLite / SQLAlchemy |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A Groq API Key (from [console.groq.com](https://console.groq.com)) or OpenCode Zen API Endpoint (`https://opencode.ai/zen/v1`)

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

### Run the Bot

```bash
python app.py
```

---

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
├── app.py                 # Bot entry point & lifecycle manager
├── bot.py                 # Telegram Application setup & handler registration
├── config.py              # Environment configuration (Pydantic Settings)
├── constants.py           # Core bot constants & defaults
├── handlers/              # Telegram update handlers
│   ├── admin_handler.py   # Admin commands & broadcast
│   ├── command_handler.py # User commands (/start, /about, /provider, /memory, etc.)
│   ├── error_handler.py   # Global error logging
│   └── message_handler.py # Main AI conversation pipeline
├── ai/                    # AI core engine
│   ├── prompt_builder.py  # System prompt generator with persona & user memory
│   ├── groq_client.py     # Groq API client with fallback & retry logic
│   ├── opencode_client.py # OpenCode Zen API client (https://opencode.ai/zen/v1)
│   ├── unified_ai_client.py# Unified AI manager & automatic failover engine
│   ├── mood_engine.py     # 9 dynamic emotional states manager
│   ├── personality_engine.py # 8 character personality profiles
│   ├── relationship_engine.py # Affinity scoring & levels
│   ├── context_builder.py # Recent message history formatter
│   ├── response_cleaner.py # Output validation & formatting
│   └── language_detector.py# Auto-detects English/Hindi/Hinglish
├── memory/                # Memory & Auto-training system
│   └── memory_manager.py  # Save, retrieve, and filter user memories
├── database/              # SQLite database layer
│   ├── engine.py          # SQLAlchemy async session setup
│   └── models.py          # User, Conversation, Memory, Preference models
├── services/              # Business logic services
├── utils/                 # Helpers, rate limiters, and validators
├── prompts/               # JSON templates for personalities, moods & prompts
├── data/                  # Runtime database file & avatars
└── tests/                 # Unit and integration test suite
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details. Created and maintained by **[Minaty001](https://github.com/Minaty001)**.

---

## 💖 Credits & Acknowledgments

Built with ❤️ by **Minaty001** using Python, Telegram Bot API, Groq AI, and OpenCode Zen.

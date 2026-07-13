# Hinata 🌸

**Your Intelligent AI Companion on Telegram**

Hinata is a warm, emotionally expressive AI companion built for Telegram. She features natural conversations, long-term memory, multiple personalities, dynamic moods, and a relationship system — all powered by Groq's free API.

---

## Features

- 💬 **Natural Conversations** — Human-like responses with emotional depth
- 🧠 **Long-Term Memory** — Remembers your preferences, facts, and history
- 🎭 **8 Personalities** — Sweet, Calm, Smart, Gamer, Playful, Curious, Boss, Supportive
- 💖 **Mood Engine** — Dynamic emotions that influence replies
- 🌱 **Relationship System** — Friendship grows naturally over time
- ⚙️ **User Settings** — Customize language, emoji level, reply length, and more
- 🌐 **Multi-Language** — English, Hindi, and Hinglish support
- 🚀 **Fast & Lightweight** — Async architecture with SQLite persistence

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.13+ |
| **Telegram** | python-telegram-bot |
| **AI** | Groq API (Free) |
| **Database** | SQLite via SQLAlchemy |
| **Validation** | Pydantic |
| **Async** | asyncio |

---

## Quick Start

### Prerequisites

- Python 3.13+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A Groq API Key (from [console.groq.com](https://console.groq.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/hinata.git
cd hinata

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your tokens
```

### Run

```bash
python app.py
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help message |
| `/about` | About Hinata |
| `/settings` | View your settings |
| `/reset` | Reset chat history |
| `/forget` | Forget specific memories |
| `/memory` | View your memories |
| `/mood` | Check current mood |
| `/personality` | Change personality |
| `/ping` | Health check |
| `/version` | Version info |

---

## Project Structure

```
Hinata/
├── app.py                 # Entry point
├── bot.py                 # Bot setup & handlers registration
├── config.py              # Configuration (pydantic-settings)
├── constants.py           # Project constants
├── handlers/              # Telegram message & command handlers
├── ai/                    # Groq client & prompt building
├── memory/                # Memory management system
├── database/              # SQLAlchemy models & engine
├── services/              # Business logic services
├── utils/                 # Helpers, validators, formatters
├── prompts/               # Personality & mood definitions (JSON)
├── data/                  # Runtime data (avatars, cache)
├── logs/                  # Application logs
├── backups/               # Database backups
└── tests/                 # Test suite
```

---

## Deployment

Hinata can be deployed on:

- **Render** / **Railway** — Easy cloud deployment
- **Docker** — Containerized deployment
- **VPS** — Traditional server deployment
- **Termux** — Run on your phone/tablet

---

## License

MIT

---

## About

Built with ❤️ using Python, Telegram, and Groq AI.

# Hinata 🌸

**FastAPI Companion AI Backend & SQLite Engine**

Hinata is a lightweight, high-performance companion AI backend built on FastAPI and SQLite. It serves as the core brain for personal client applications (such as a Flutter mobile APK) to manage chatting, memory, voice transcription/synthesis, settings, and productivity tools in a fully unauthenticated, single-user mode.

---

## 🌟 Key Highlights

- 🧠 **Relational AI Core** — Houses feeling classification, defense detection, mood shifts, and personality styling under a unified personal AI brain.
- 💾 **Long-Term Memory & Context** — Automatically manages fact retrieval, decay, and decay-aware search queries.
- ⚡ **6 AI LLM Providers** — Supports Groq, OpenCode Zen, OpenAI, Gemini, OpenRouter, and Bytez with zero-downtime failover logic.
- 👤 **Local User Mode** — Streamlined for personal deployment; no authentication (JWT/bcrypt) or register gates required. Every request acts on a single default `local` user profile.
- 🎤 **Voice Integration** — Native endpoints for speech-to-text (transcription) and text-to-speech (synthesis).
- 📅 **Productivity Engine** — Endpoints for task tracking, scheduling events, and managing target goals.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| **Backend Framework** | Python 3.12+ (FastAPI) |
| **Server** | Uvicorn |
| **Database** | SQLite via SQLAlchemy 2.0 (Async Engine & aiosqlite) |
| **Validation** | Pydantic Settings & Schemas |
| **AI LLM APIs** | Groq, OpenCode Zen, OpenAI, Gemini, OpenRouter, Bytez |

---

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Minaty001/hinata.git
   cd hinata
   ```

2. **Set up virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Open .env and set your GROQ_API_KEY / chosen AI_PROVIDER keys
   ```

5. **Start server:**
   ```bash
   ./start.sh
   ```

---

## 📂 Project Structure

```text
Hinata/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI server setup & routing
│   │   ├── api/                 # REST endpoints (chat, memory, voice, settings, productivity)
│   │   ├── core/                # Brain, user manager, configuration, constants
│   │   ├── database/            # SQLite engine and SQLAlchemy models
│   │   ├── memory/              # Cosine similarity decay-aware memory manager
│   │   ├── services/            # Chat & user preference services
│   │   ├── schemas/             # Pydantic schema validation models
│   │   ├── training/            # Feature embedder & quality scorers
│   │   └── voice/               # Speech-to-text and text-to-speech engine
│   └── requirements.txt         # Backend python dependencies
├── ai/                          # Shared personal AI engine classifiers and clients
├── prompts/                     # Dynamic personality & mood prompt templates
├── tests/                       # Pytest integration tests
├── .env.example                 # Configuration template
├── start.sh                     # Startup script
└── README.md                    # Project documentation
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details. Created and maintained by **[Minaty001](https://github.com/Minaty001)**.

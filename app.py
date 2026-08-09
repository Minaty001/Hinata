"""
Hinata Hyuga - Web Application & Deep Search Server (app.py)

Dedicated entry point for the Hinata Hyuga Web Application UI:
- Serves static assets from web/ (index.html, style.css, app.js)
- REST APIs:
  - POST /api/chat — Real-time AI companion chat completions
  - GET  /api/search — Deep Search engine query handler
  - GET  /api/memories — User memories API
  - POST /api/provider — AI provider & model switcher (Groq / OpenCode Zen)
  - GET  /api/status — Application status & model catalog

Usage:
    python app.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
import sys


from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

from ai.mood_engine import MoodState, MoodEngine
from ai.prompt_builder import PromptBuilder
from ai.unified_ai_client import UnifiedAIClient
from ai.feeling_detector import FeelingDetector
from ai.need_analyzer import NeedAnalyzer
from ai.defense_detector import DefenseDetector
from ai.response_mode_selector import ResponseModeSelector
from ai.distress_detector import detect_distress
from ai.vulnerability_scaffold import get_scaffold_instructions
from ai.relationship_engine import RelationshipEngine
from ai.personality_engine import PersonalityEngine

from config import settings
from constants import (
    BOT_NAME,
    BOT_VERSION,
    LOGS_DIR,
    OPENCODE_ZEN_FREE_MODELS,
)

import urllib.parse
from sqlalchemy import select
from database.database import async_session_factory, init_database
from services.user_service import get_or_create_web_user
from services.chat_service import (
    save_message,
    get_conversation_history,
    get_user_chains,
    get_or_create_chain,
    delete_chain,
    auto_index_session,
    get_session_indices,
    search_session_indices,
)
from memory.memory_manager import get_memories_list, get_memories_summary, save_memory
from ai.context_builder import build_conversation_context
from database.models import Conversation, Memory, Setting, SessionIndex
from training.behavioral_tracker import BehavioralTracker
from training.quality_scorer import QualityScorer
from training.conversation_encoder import ConversationEncoder


async def load_settings_from_db():
    """Load saved AI provider API keys, base URLs, models, and active provider from database."""
    async with async_session_factory() as session:
        stmt = select(Setting)
        res = await session.execute(stmt)
        for setting in res.scalars().all():
            if setting.key == "active_provider":
                unified_ai_client.set_active_provider(setting.value)
            elif setting.key.startswith("provider_"):
                parts = setting.key.split("_")
                field = parts[-1]
                prov_key = "_".join(parts[1:-1])
                if field == "key":
                    unified_ai_client.set_provider_config(prov_key, api_key=setting.value)
                elif field == "url":
                    unified_ai_client.set_provider_config(prov_key, base_url=setting.value)
                elif field == "model":
                    unified_ai_client.set_provider_config(prov_key, model=setting.value)


async def save_setting_to_db(key: str, value: str):
    """Save setting key-value pair to database."""
    async with async_session_factory() as session:
        stmt = select(Setting).where(Setting.key == key)
        res = await session.execute(stmt)
        setting = res.scalar_one_or_none()
        if setting:
            setting.value = value
        else:
            setting = Setting(key=key, value=value)
            session.add(setting)
        await session.commit()


PROJECT_ROOT = Path(__file__).resolve().parent
WEB_DIR = PROJECT_ROOT / "web"

# Logging setup
LOGS_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "webapp.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── CORS configuration ────────────────────────────────────────────────────
# Set WEB_ORIGINS to a comma-separated list of allowed origins.
# In production, this must be set explicitly (e.g., https://your-domain.com).
# Wildcard (*) is intentionally disabled.
_WEB_ORIGINS: set[str] = {
    o.strip()
    for o in os.getenv("WEB_ORIGINS", "http://localhost:2027,http://127.0.0.1:2027").split(",")
    if o.strip()
}

# Shared AI Client & Prompt Builder
unified_ai_client = UnifiedAIClient()
prompt_builder = PromptBuilder()

# Next-Level AI Engines
feeling_detector = FeelingDetector()
need_analyzer = NeedAnalyzer()
defense_detector = DefenseDetector()
response_selector = ResponseModeSelector()
behavioral_tracker = BehavioralTracker()
quality_scorer = QualityScorer()
conversation_encoder = ConversationEncoder()


def _run_async(coro):
    """Run an async coroutine synchronously in an isolated event loop."""
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class HinataWebRequestHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler for Hinata Web Application UI & REST APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self) -> None:
        """Route GET requests to API handlers or static files."""
        if self.path.startswith("/api/chains") or self.path.startswith("/api/sessions"):
            self._handle_api_get_chains()
        elif self.path.startswith("/api/session/index"):
            self._handle_api_get_session_index()
        elif self.path.startswith("/api/history"):
            self._handle_api_get_history()
        elif self.path.startswith("/api/search"):
            self._handle_api_search()
        elif self.path.startswith("/api/memories"):
            self._handle_api_memories()
        elif self.path.startswith("/api/providers"):
            self._handle_api_get_providers()
        elif self.path.startswith("/api/status"):
            self._handle_api_status()
        else:
            super().do_GET()

    def do_POST(self) -> None:
        """Route POST requests to REST API handlers."""
        if self.path == "/api/chat":
            self._handle_api_chat()
        elif self.path.startswith("/api/chains") or self.path.startswith("/api/sessions"):
            self._handle_api_create_chain()
        elif self.path == "/api/memories":
            self._handle_api_add_memory()
        elif self.path == "/api/provider":
            self._handle_api_provider()
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_DELETE(self) -> None:
        """Route DELETE requests."""
        if self.path.startswith("/api/chains") or self.path.startswith("/api/sessions"):
            self._handle_api_delete_chain()
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests — only allow configured origins."""
        origin = self.headers.get("Origin", "")
        self.send_response(204)
        if origin in _WEB_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()


    def _handle_api_get_chains(self) -> None:
        """Return list of conversation chains/sessions for web user."""
        async def _impl():
            async with async_session_factory() as session:
                user = await get_or_create_web_user(session)
                return await get_user_chains(session, user.id)

        try:
            chains = _run_async(_impl())
            self._send_json({"status": "success", "chains": chains, "sessions": chains})
        except Exception as exc:
            logger.exception("Error getting chains: %s", exc)
            self._send_json({"error": str(exc)}, status=500)

    def _handle_api_get_session_index(self) -> None:
        """Return session topic index entries for fast lookup."""
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        chain_id = qs.get("chain_id", [""])[0]

        if not chain_id:
            self._send_json({"error": "Missing chain_id"}, status=400)
            return

        async def _impl():
            async with async_session_factory() as session:
                return await get_session_indices(session, chain_id)

        try:
            indices = _run_async(_impl())
            self._send_json({"status": "success", "chain_id": chain_id, "indices": indices})
        except Exception as exc:
            logger.exception("Error getting session index: %s", exc)
            self._send_json({"error": str(exc)}, status=500)

    def _handle_api_create_chain(self) -> None:
        """Create a new conversation chain/session."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        data = json.loads(body.decode("utf-8"))
        title = data.get("title", "New Session")

        async def _impl():
            async with async_session_factory() as session:
                user = await get_or_create_web_user(session)
                c = await get_or_create_chain(session, user.id, title=title)
                return {"chain_id": c.chain_id, "session_id": c.chain_id, "title": c.title}

        try:
            res = _run_async(_impl())
            self._send_json({"status": "success", "chain": res, "session": res})
        except Exception as exc:
            logger.exception("Error creating chain: %s", exc)
            self._send_json({"error": str(exc)}, status=500)

    def _handle_api_delete_chain(self) -> None:
        """Delete a conversation chain/session."""
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        chain_id = qs.get("chain_id", [qs.get("session_id", [""])[0]])[0]

        if not chain_id:
            self._send_json({"error": "Missing chain_id or session_id"}, status=400)
            return

        async def _impl():
            async with async_session_factory() as session:
                user = await get_or_create_web_user(session)
                return await delete_chain(session, user.id, chain_id)

        try:
            success = _run_async(_impl())
            self._send_json({"status": "success", "deleted": success})
        except Exception as exc:
            logger.exception("Error deleting chain: %s", exc)
            self._send_json({"error": str(exc)}, status=500)

    def _handle_api_get_history(self) -> None:
        """Return history for a specific conversation chain/session."""
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        chain_id = qs.get("chain_id", [qs.get("session_id", [None])[0]])[0]

        async def _impl():
            async with async_session_factory() as session:
                user = await get_or_create_web_user(session)
                chains = await get_user_chains(session, user.id)
                target_chain_id = chain_id or (chains[0]["chain_id"] if chains else None)
                msgs = await get_conversation_history(session, user.id, chain_id=target_chain_id, limit=100)
                indices = await get_session_indices(session, target_chain_id) if target_chain_id else []
                return target_chain_id, [
                    {
                        "id": m.id,
                        "role": m.role,
                        "message": m.message,
                        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    }
                    for m in msgs
                ], indices

        try:
            active_chain_id, history, indices = _run_async(_impl())
            self._send_json({"status": "success", "chain_id": active_chain_id, "session_id": active_chain_id, "messages": history, "indices": indices})
        except Exception as exc:
            logger.exception("Error getting history: %s", exc)
            self._send_json({"error": str(exc)}, status=500)

    def _handle_api_chat(self) -> None:
        """Process chat completion requests and store in DB with auto session indexing."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data: dict[str, Any] = json.loads(body.decode("utf-8"))
            user_message = data.get("message", "").strip()
            provider = data.get("provider")
            model = data.get("model")
            chain_id = data.get("chain_id", data.get("session_id"))

            if not user_message:
                self._send_json({"error": "Empty message"}, status=400)
                return

            if provider:
                unified_ai_client.set_active_provider(provider, model)

            async def _process_db_chat():
                async with async_session_factory() as session:
                    user = await get_or_create_web_user(session)
                    active_chain = await get_or_create_chain(session, user.id, chain_id=chain_id)
                    actual_chain_id = active_chain.chain_id

                    # 1. Store user message in DB
                    await save_message(session, user.id, "user", user_message, chain_id=actual_chain_id)

                    # 2. Get past conversation context & session topic index for prompt
                    conv_context = await build_conversation_context(session, user.id, chain_id=actual_chain_id)

                    # 3. Get user memories
                    memories_text = await get_memories_summary(session, user.id)

                    # 4. Feeling detection (next-level)
                    detected_feeling = feeling_detector.detect(user_message)
                    need_result = need_analyzer.analyze(detected_feeling, user_message)
                    defense_result = defense_detector.detect(user_message)

                    # 5. Distress detection & CARE protocol (aligning with Telegram)
                    distress_result = detect_distress(
                        user_message,
                        feeling_valence=detected_feeling.get("valence"),
                    )
                    care_instructions = distress_result.get("care_instructions", "")

                    # 6. Response mode selection
                    rel_engine = RelationshipEngine()
                    personality_engine = PersonalityEngine()
                    mood_engine = MoodEngine()

                    rel_level = rel_engine.get_level(user.relationship_score)
                    selected_mode = response_selector.select(
                        feeling=detected_feeling,
                        need_result=need_result,
                        relationship_level=rel_level,
                        interaction_count=user.relationship_score,
                    )
                    mode_id = selected_mode.get("id", "comfort")
                    mode_instructions = response_selector.get_instructions(mode_id)

                    # 7. Personality, mood and relationship instructions
                    personality = personality_engine.get_personality(user.current_personality or "sweet")
                    personality_instructions = personality_engine.get_instructions(user.current_personality or "sweet")

                    mood = mood_engine.determine_mood(
                        current_mood=user.current_mood,
                        relationship_score=user.relationship_score,
                    )
                    mood_instructions = mood_engine.get_instructions(mood)

                    rel_instructions = rel_engine.get_instructions(user.relationship_score)

                    # 8. Build system prompt
                    act_prov = unified_ai_client.get_active_provider()
                    enhanced_mood = (
                        f"{mood_instructions}\n\n"
                        f"Response Mode: {selected_mode.get('name', 'Comfort')}\n"
                        f"{mode_instructions}"
                    )
                    if care_instructions:
                        enhanced_mood += f"\n\nCARE PROTOCOL ACTIVE:\n{care_instructions}"
                    if defense_result.get("primary", "none") != "none":
                        enhanced_mood += f"\n\nDefense strategy: {defense_result.get('strategy', '')}"

                    scaffold_instructions = get_scaffold_instructions(rel_level)

                    system_prompt = prompt_builder.build_system_prompt(
                        personality_name=(user.current_personality or "sweet").capitalize(),
                        personality=personality,
                        mood_name=mood.name,
                        mood=mood,
                        relationship_level=rel_level,
                        relationship_instructions=rel_instructions,
                        user_name=user.display_name or "User",
                        language=user.language or "hinglish",
                        preferences="- Preferred Engine: " + act_prov,
                        memories=memories_text,
                        personality_instructions=personality_instructions,
                        mood_instructions=enhanced_mood,
                        scaffold_instructions=scaffold_instructions,
                    )

                    messages = prompt_builder.build_messages(
                        system_prompt=system_prompt,
                        conversation_context=conv_context,
                        user_message=user_message,
                    )

                    # 9. Call AI completion
                    mode_temp = response_selector.get_temperature(mode_id)
                    ai_reply = await unified_ai_client.chat_completion(
                        messages, model=model, temperature=mode_temp
                    )

                    # 10. Save assistant message to DB
                    await save_message(session, user.id, "assistant", ai_reply, chain_id=actual_chain_id)

                    # 11. Update relationship score & mood in DB (aligning with Telegram)
                    increase = rel_engine.calculate_score_increase(
                        len(user_message),
                        user.relationship_score,
                    )
                    user.relationship_score += increase
                    user.current_mood = mood.name

                    # 12. Auto-index session topics for fast proceed lookup
                    await auto_index_session(session, user.id, actual_chain_id)

                    # Persist score/mood — auto_index often no-ops without committing
                    await session.commit()

                    return actual_chain_id, ai_reply


            actual_chain_id, ai_reply = _run_async(_process_db_chat())

            act_p = unified_ai_client.get_active_provider()
            act_m = unified_ai_client.providers[act_p]["active_model"]

            self._send_json({
                "status": "success",
                "reply": ai_reply,
                "chain_id": actual_chain_id,
                "session_id": actual_chain_id,
                "provider": act_p,
                "model": act_m,
            })

        except Exception as exc:
            logger.exception("Error in /api/chat: %s", exc)
            act_p = unified_ai_client.get_active_provider()
            act_m = unified_ai_client.providers.get(act_p, {}).get("active_model", "default")
            self._send_json({
                "status": "fallback",
                "reply": f"Arre re! Koi baat nahi ji, main Hinata hoon! Kaise ho aap? 🌸 (Provider: {act_p}, Model: {act_m})",
            })

    def _handle_api_search(self) -> None:
        """Execute Deep Search query across database conversations, topic indices, memories, and settings."""
        parsed = urllib.parse.urlparse(self.path)
        qs = urllib.parse.parse_qs(parsed.query)
        query = qs.get("q", [""])[0].strip()

        if not query:
            self._send_json({"query": "", "results": []})
            return

        escaped_query = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


        async def _impl():
            async with async_session_factory() as session:
                user = await get_or_create_web_user(session)
                results = []

                # 1. Search Session Topic Index for direct topic jump (ChatGPT-style page index)
                indexed_results = await search_session_indices(session, user.id, query)
                for idx_item in indexed_results:
                    results.append({
                        "category": "sessions",
                        "title": f"Topic Page {idx_item['page_number']}: {idx_item['topic']}",
                        "snippet": f"Session: {idx_item['chain_title']} | Summary: {idx_item['summary']}",
                        "chain_id": idx_item["chain_id"],
                        "session_id": idx_item["chain_id"],
                    })

                # 2. Search Conversations table
                conv_stmt = select(Conversation).where(
                    Conversation.user_id == user.id,
                    Conversation.message.ilike(f"%{escaped_query}%", escape="\\")
                ).limit(10)
                conv_res = await session.execute(conv_stmt)
                for msg in conv_res.scalars().all():
                    results.append({
                        "category": "conversations",
                        "title": f"Chat Message ({msg.role})",
                        "snippet": msg.message[:120],
                        "chain_id": msg.chain_id,
                        "session_id": msg.chain_id,
                    })

                # 3. Search Memory table
                mem_stmt = select(Memory).where(
                    Memory.user_id == user.id,
                    Memory.content.ilike(f"%{escaped_query}%", escape="\\")
                ).limit(10)
                mem_res = await session.execute(mem_stmt)
                for mem in mem_res.scalars().all():
                    results.append({
                        "category": "memory",
                        "title": f"Memory [{mem.type}]",
                        "snippet": mem.content,
                    })


                # 4. Model matches across all providers
                providers_info = unified_ai_client.get_all_providers_info()
                for p_key, p_val in providers_info.items():
                    for m in p_val["models"]:
                        if query.lower() in m.lower():
                            results.append({
                                "category": "models",
                                "title": f"[{p_val['name']}] {m}",
                                "snippet": f"Base URL: {p_val['base_url']}",
                            })

                return results

        try:
            results = _run_async(_impl())
            self._send_json({"query": query, "results": results})
        except Exception as exc:
            logger.exception("Error in /api/search: %s", exc)
            self._send_json({"query": query, "results": []})

    def _handle_api_memories(self) -> None:
        """Return list of user memories from SQLite database."""
        async def _impl():
            async with async_session_factory() as session:
                user = await get_or_create_web_user(session)
                return await get_memories_list(session, user.id)

        try:
            memories = _run_async(_impl())
            self._send_json({"memories": memories})
        except Exception as exc:
            logger.exception("Error reading memories: %s", exc)
            self._send_json({"memories": []})

    def _handle_api_add_memory(self) -> None:
        """Add a memory entry manually from UI."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        data = json.loads(body.decode("utf-8"))
        mem_type = data.get("type", "fact")
        content = data.get("content", "").strip()

        if not content:
            self._send_json({"error": "Empty content"}, status=400)
            return

        async def _impl():
            async with async_session_factory() as session:
                user = await get_or_create_web_user(session)
                m = await save_memory(session, user.id, mem_type, content, importance=5)
                return {"id": m.id, "type": m.type, "content": m.content}

        try:
            res = _run_async(_impl())
            self._send_json({"status": "success", "memory": res})
        except Exception as exc:
            logger.exception("Error adding memory: %s", exc)
            self._send_json({"error": str(exc)}, status=500)

    def _handle_api_get_providers(self) -> None:
        """Return status and configuration for all 6 AI providers."""
        info = unified_ai_client.get_all_providers_info()
        self._send_json({"status": "success", "active_provider": unified_ai_client.get_active_provider(), "providers": info})

    def _handle_api_provider(self) -> None:
        """Set active AI provider, model, API key, base URL, and save to DB."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        data = json.loads(body.decode("utf-8"))

        provider = data.get("provider")
        model = data.get("model")
        api_key = data.get("api_key")
        base_url = data.get("base_url")

        async def _impl():
            if provider:
                unified_ai_client.set_active_provider(provider, model)
                await save_setting_to_db("active_provider", provider)

            target_prov = provider or unified_ai_client.get_active_provider()
            if api_key is not None or base_url is not None or model is not None:
                unified_ai_client.set_provider_config(target_prov, api_key=api_key, base_url=base_url, model=model)
                if api_key is not None:
                    await save_setting_to_db(f"provider_{target_prov}_key", api_key)
                if base_url is not None:
                    await save_setting_to_db(f"provider_{target_prov}_url", base_url)
                if model is not None:
                    await save_setting_to_db(f"provider_{target_prov}_model", model)

            return unified_ai_client.get_all_providers_info()

        try:
            all_info = _run_async(_impl())
            self._send_json({"status": "success", "active_provider": unified_ai_client.get_active_provider(), "providers": all_info})
        except Exception as exc:
            logger.exception("Error in /api/provider: %s", exc)
            self._send_json({"error": str(exc)}, status=500)

    def _handle_api_status(self) -> None:
        """Return Web App status."""
        self._send_json({
            "name": BOT_NAME,
            "version": BOT_VERSION,
            "active_provider": unified_ai_client.get_active_provider(),
            "providers": unified_ai_client.get_all_providers_info(),
        })

    def log_error(self, format: str, *args: Any) -> None:
        """Catch and cleanly log HTTPS connection attempts on plain HTTP port."""
        msg = format % args if args else format
        if any(err in msg for err in ("Bad request version", "Bad HTTP", "Bad request syntax")):
            logger.warning("[Notice] HTTPS connection attempt detected on HTTP port. Please use http:// (not https://).")
            print("\n⚠️ [NOTICE] HTTPS connection attempt detected!")
            print("👉 Please open URL using HTTP (not HTTPS):")
            print(f"   Correct: http://{get_local_ip()}:2027\n")
            return
        super().log_error(format, *args)

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        """Send JSON HTTP response with configurable CORS headers."""
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        origin = self.headers.get("Origin", "")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        if origin in _WEB_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body_bytes)


def get_local_ip() -> str:
    """Detect local Wi-Fi / LAN IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"



def run_web_app(host: str = "0.0.0.0", port: int = 2027) -> None:
    """Start the Hinata Hyuga Web Application server."""
    # Ensure SQLite tables exist and load saved settings from database
    import database.models  # noqa: F401
    _run_async(init_database())
    _run_async(load_settings_from_db())

    server_address = (host, port)
    httpd = HTTPServer(server_address, HinataWebRequestHandler)
    local_ip = get_local_ip()

    logger.info("Hinata Hyuga Web Application running on http://localhost:%d and http://%s:%d", port, local_ip, port)
    print("\n" + "=" * 60)
    print("🌸 Hinata Hyuga Web Application & Deep Search Engine 🌸")
    print("=" * 60)
    print(f"💻 Local Machine Access : http://localhost:{port}")
    print(f"📱 Android / Wi-Fi Access: http://{local_ip}:{port}")
    print("=" * 60)
    print("⚠️  IMPORTANT: Use http:// (NOT https://) in your phone browser!")
    print(f"👉 OPEN IN BROWSER: http://{local_ip}:{port}")
    print("=" * 60 + "\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Hinata Web Application server.")
        httpd.server_close()


if __name__ == "__main__":
    default_host = getattr(settings, "WEB_HOST", "0.0.0.0")
    default_port = getattr(settings, "WEB_PORT", 2027)
    host_arg = os.getenv("WEB_HOST", default_host)
    port_arg = int(os.getenv("WEB_PORT", str(default_port)))
    for arg in sys.argv:
        if arg.startswith("--port="):
            try:
                port_arg = int(arg.split("=")[1])
            except ValueError:
                pass
        elif arg.startswith("--host="):
            host_arg = arg.split("=")[1]
    run_web_app(host=host_arg, port=port_arg)


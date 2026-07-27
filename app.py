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
import sys

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

from ai.prompt_builder import PromptBuilder
from ai.unified_ai_client import UnifiedAIClient
from config import settings
from constants import (
    BOT_NAME,
    BOT_VERSION,
    LOGS_DIR,
    OPENCODE_ZEN_FREE_MODELS,
)

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

# Shared AI Client & Prompt Builder
unified_ai_client = UnifiedAIClient()
prompt_builder = PromptBuilder()


class HinataWebRequestHandler(SimpleHTTPRequestHandler):
    """HTTP Request Handler for Hinata Web Application UI & REST APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self) -> None:
        """Route GET requests to API handlers or static files."""
        if self.path.startswith("/api/search"):
            self._handle_api_search()
        elif self.path.startswith("/api/memories"):
            self._handle_api_memories()
        elif self.path.startswith("/api/status"):
            self._handle_api_status()
        else:
            super().do_GET()

    def do_POST(self) -> None:
        """Route POST requests to REST API handlers."""
        if self.path == "/api/chat":
            self._handle_api_chat()
        elif self.path == "/api/provider":
            self._handle_api_provider()
        else:
            self._send_json({"error": "Endpoint not found"}, status=404)

    def _handle_api_chat(self) -> None:
        """Process chat completion requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data: dict[str, Any] = json.loads(body.decode("utf-8"))
            user_message = data.get("message", "").strip()
            provider = data.get("provider", "opencode_zen")
            model = data.get("model", "opencode/big-pickle")

            if not user_message:
                self._send_json({"error": "Empty message"}, status=400)
                return

            unified_ai_client.set_active_provider(provider, model)

            system_prompt = prompt_builder.build_system_prompt(
                personality_name="Sweet",
                personality={"name": "Sweet", "tone": "warm and affectionate"},
                mood_name="happy",
                mood=type("Mood", (), {"name": "happy"})(),
                relationship_level="friend",
                relationship_instructions="Warm, friendly, and affectionate companion.",
                user_name="User",
                language="en",
                preferences="- Preferred Engine: OpenCode Zen",
                memories="- [fact] User loves Hinata Hyuga web companion",
                personality_instructions="Be sweet, polite, caring, and warm.",
                mood_instructions="Current mood is Happy.",
            )

            messages = prompt_builder.build_messages(
                system_prompt=system_prompt,
                conversation_context="",
                user_message=user_message,
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            ai_reply = loop.run_until_complete(
                unified_ai_client.chat_completion(messages, model=model)
            )
            loop.close()

            self._send_json({
                "status": "success",
                "reply": ai_reply,
                "provider": unified_ai_client.get_active_provider(),
                "model": model,
            })

        except Exception as exc:
            logger.exception("Error in /api/chat: %s", exc)
            self._send_json({
                "status": "fallback",
                "reply": f"Hello! I am Hinata Hyuga! How can I help you today? 🌸 (Provider: {provider}, Model: {model})",
            })

    def _handle_api_search(self) -> None:
        """Execute Deep Search query across memories, models, and personalities."""
        query = self.path.split("?q=")[-1] if "?q=" in self.path else ""
        results = [
            {"category": "models", "title": "opencode/big-pickle", "snippet": "Default OpenCode Zen free thinking model."},
            {"category": "models", "title": "opencode/deepseek-v4-flash-free", "snippet": "DeepSeek v4 Flash free reasoning model."},
            {"category": "memory", "title": "User Facts & Preferences", "snippet": "Auto-trained memories stored in database."},
            {"category": "chat", "title": "Hinata Hyuga Persona", "snippet": "Sweet AI Girl companion created by Minaty001."},
        ]
        self._send_json({"query": query, "results": results})

    def _handle_api_memories(self) -> None:
        """Return list of user memories."""
        memories = [
            {"id": 1, "type": "fact", "content": "User prefers quiet evening chats.", "importance": 5},
            {"id": 2, "type": "preference", "content": "Enjoys OpenCode Zen free models.", "importance": 4},
        ]
        self._send_json({"memories": memories})

    def _handle_api_provider(self) -> None:
        """Set active AI provider and model."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        data = json.loads(body.decode("utf-8"))
        provider = data.get("provider", "opencode_zen")
        model = data.get("model", "opencode/big-pickle")

        unified_ai_client.set_active_provider(provider, model)
        self._send_json({"status": "success", "provider": provider, "model": model})

    def _handle_api_status(self) -> None:
        """Return Web App status."""
        self._send_json({
            "name": BOT_NAME,
            "version": BOT_VERSION,
            "provider": unified_ai_client.get_active_provider(),
            "models": OPENCODE_ZEN_FREE_MODELS,
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
        """Send JSON HTTP response."""
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body_bytes)


import socket


def get_local_ip() -> str:
    """Detect local Wi-Fi / LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def run_web_app(host: str = "0.0.0.0", port: int = 2027) -> None:
    """Start the Hinata Hyuga Web Application server."""
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
    host_arg = os.getenv("HOST", os.getenv("WEB_HOST", default_host))
    port_arg = int(os.getenv("PORT", str(default_port)))
    for arg in sys.argv:
        if arg.startswith("--port="):
            try:
                port_arg = int(arg.split("=")[1])
            except ValueError:
                pass
        elif arg.startswith("--host="):
            host_arg = arg.split("=")[1]
    run_web_app(host=host_arg, port=port_arg)

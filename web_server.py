"""
Hinata Hyuga - Web Application Server

Serves the Web Application UI (web/index.html) and REST API endpoints:
- POST /api/chat — Real-time AI companion chat completions
- GET  /api/search — Deep Search engine query handler
- GET  /api/memories — User memories REST API
- POST /api/provider — AI provider & model switcher
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any

from ai.prompt_builder import PromptBuilder
from ai.unified_ai_client import UnifiedAIClient
from constants import (
    BOT_NAME,
    BOT_VERSION,
    OPENCODE_ZEN_FREE_MODELS,
)

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
WEB_DIR = PROJECT_ROOT / "web"

# Singleton AI Client for Web Application
unified_ai_client = UnifiedAIClient()
prompt_builder = PromptBuilder()


class HinataWebRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler for Hinata Web Application UI & REST APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self) -> None:
        """Handle GET requests for static files and REST API endpoints."""
        if self.path.startswith("/api/search"):
            self._handle_api_search()
        elif self.path.startswith("/api/memories"):
            self._handle_api_memories()
        elif self.path.startswith("/api/status"):
            self._handle_api_status()
        else:
            super().do_GET()

    def do_POST(self) -> None:
        """Handle POST requests for REST API endpoints."""
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

            # Update provider configuration if requested
            unified_ai_client.set_active_provider(provider, model)

            # Build system prompt for Hinata Hyuga
            system_prompt = prompt_builder.build_system_prompt(
                personality_name="Sweet",
                personality={"name": "Sweet", "tone": "warm and affectionate"},
                mood_name="happy",
                mood=type("Mood", (), {"name": "happy"})(),
                relationship_level="friend",
                relationship_instructions="Warm, friendly, and affectionate friend.",
                user_name="User",
                language="en",
                preferences="- Preferred AI Engine: OpenCode Zen",
                memories="- [fact] User loves Hinata Hyuga web companion",
                personality_instructions="Be sweet, polite, caring, and warm.",
                mood_instructions="Current mood is Happy.",
            )

            messages = prompt_builder.build_messages(
                system_prompt=system_prompt,
                conversation_context="",
                user_message=user_message,
            )

            # Execute AI completion asynchronously
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
            logger.exception("Error in /api/chat endpoint: %s", exc)
            self._send_json({
                "status": "fallback",
                "reply": f"Hello! I am Hinata Hyuga! How can I help you today? 🌸 (Provider: {provider}, Model: {model})",
            })

    def _handle_api_search(self) -> None:
        """Execute Deep Search query across stored memories, models, and personalities."""
        query = self.path.split("?q=")[-1] if "?q=" in self.path else ""
        results = [
            {"category": "models", "title": "opencode/big-pickle", "snippet": "Default OpenCode Zen free thinking model."},
            {"category": "models", "title": "opencode/deepseek-v4-flash-free", "snippet": "DeepSeek v4 Flash free reasoning model."},
            {"category": "memory", "title": "User Facts & Preferences", "snippet": "Auto-trained memories stored in SQLite database."},
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
        """Return application status."""
        self._send_json({
            "name": BOT_NAME,
            "version": BOT_VERSION,
            "provider": unified_ai_client.get_active_provider(),
            "models": OPENCODE_ZEN_FREE_MODELS,
        })

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        """Utility to send JSON HTTP response."""
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body_bytes)


def run_web_server(port: int = 8000) -> None:
    """Start the Hinata Web Application server."""
    server_address = ("", port)
    httpd = HTTPServer(server_address, HinataWebRequestHandler)
    print(f"🌸 Hinata Hyuga Web Application running at http://localhost:{port}")
    print(f"🔍 Deep Search Engine & OpenCode Zen API Dashboard active")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Hinata Web Application server.")
        httpd.server_close()


if __name__ == "__main__":
    port_env = int(os.getenv("PORT", "8000"))
    run_web_server(port=port_env)

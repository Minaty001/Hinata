"""
Hinata Reflex Brain — Executor

Dispatches matched reflex commands to target devices via active WebSockets
and returns localized confirmation strings.
"""
from __future__ import annotations

import logging
from typing import Any

from app.api.websocket import manager as ws_manager
from app.database.models import User
from app.reflex.classifier import ReflexMatch

logger = logging.getLogger(__name__)


class ReflexExecutor:
    """Executes reflex matches by sending payloads to active WebSocket clients."""

    async def execute(
        self,
        match: ReflexMatch,
        user: User,
    ) -> dict[str, Any]:
        """Dispatch command to user device WebSocket and return result dictionary."""
        command_payload = {
            "type": "command",
            "command": match.command,
            "arguments": match.arguments,
        }

        # Dispatch command via active WebSockets for user
        dispatched = await ws_manager.send_to_user(user.id, command_payload)
        
        reply_message = match.get_reply()
        
        if dispatched:
            logger.info("Successfully dispatched reflex command '%s' to user_id=%d", match.command, user.id)
        else:
            logger.warning(
                "Reflex command '%s' resolved, but user_id=%d has no active WebSocket connection. "
                "Output reply returned, execution will complete on client reconnection.",
                match.command,
                user.id,
            )

        return {
            "reply": reply_message,
            "dispatched": dispatched,
            "command": match.command,
            "arguments": match.arguments,
        }

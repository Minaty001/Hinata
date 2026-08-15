"""
Hinata Backend — WebSocket Manager & Connection Registry

Maintains persistent duplex connections for real-time streaming, pairing, and
direct device-control command dispatch.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.user import get_default_user
from app.database.engine import get_session

logger = logging.getLogger(__name__)
router = APIRouter()


class WebSocketConnectionManager:
    """Manages active WebSocket connections keyed by the default user ID."""

    def __init__(self) -> None:
        # Map user_id -> set of active WebSocket instances
        self.active_connections: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        """Accept connection and register it in memory."""
        await websocket.accept()
        self.active_connections.setdefault(user_id, set()).add(websocket)
        logger.info("WebSocket connected for user_id=%d. Total active sockets: %d", user_id, len(self.active_connections[user_id]))

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        """Deregister active connection."""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            logger.info("WebSocket disconnected for user_id=%d", user_id)

    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> bool:
        """Send JSON payload to all active WebSocket connections for a user.

        Returns True if at least one message was sent successfully.
        """
        sockets = self.active_connections.get(user_id, set())
        if not sockets:
            logger.warning("No active WebSocket connections found for user_id=%d", user_id)
            return False

        success = False
        message_str = json.dumps(payload)
        for ws in list(sockets):
            try:
                await ws.send_text(message_str)
                success = True
            except Exception as exc:
                logger.error("Failed to send socket payload to user_id=%d: %s", user_id, exc)
                self.disconnect(user_id, ws)
        return success


manager = WebSocketConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db_session: AsyncSession = Depends(get_session)):
    """Duplex WebSocket endpoint — always connects as the local default user."""
    user = await get_default_user(db_session)
    await db_session.commit()
    user_id = user.id

    await manager.connect(user_id, websocket)
    try:
        while True:
            # Maintain connection, handle incoming client messages (e.g. heartbeat or confirmations)
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
                logger.debug("Received WebSocket data from user_id=%d: %s", user_id, data)

                # Echo check or keepalive ping-pong
                if data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                # Fallback echo for legacy standard text clients
                await websocket.send_text(f"Echo: {data_str}")
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as exc:
        logger.error("Error in WebSocket thread for user_id=%d: %s", user_id, exc)
        manager.disconnect(user_id, websocket)

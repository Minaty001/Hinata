"""
Hinata Backend — WebSocket Manager & Connection Registry

Maintains persistent duplex connections for real-time streaming, pairing, and
direct device-control command dispatch.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.core.security import decode_token
from app.database.engine import AsyncSessionMaker
from app.database.models import User, UserSession

logger = logging.getLogger(__name__)
router = APIRouter()


class WebSocketConnectionManager:
    """Manages active WebSocket connections keyed by authenticated user ID."""

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
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """Duplex WebSocket endpoint with JWT session verification."""
    # Read token from query parameters if not passed in header (common for browser WebSockets)
    if not token:
        token = websocket.query_params.get("token")

    if not token:
        logger.warning("WebSocket connection rejected: Missing authorization token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Authenticate token and load user session
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub", 0))
        jti = payload.get("jti")
        
        if not user_id or not jti or payload.get("type") != "access":
            logger.warning("WebSocket connection rejected: Invalid token claims")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Check session state in DB
        async with AsyncSessionMaker() as db_session:
            stmt = select(UserSession).where(UserSession.jti == jti)
            result = await db_session.execute(stmt)
            user_session = result.scalars().first()
            
            if not user_session or user_session.is_revoked:
                logger.warning("WebSocket connection rejected: Session is revoked or missing")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

    except Exception as exc:
        logger.warning("WebSocket authentication failed: %s", exc)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Successfully authenticated
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

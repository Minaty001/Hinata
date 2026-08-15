"""
Tests for the /ws WebSocket endpoint (no-auth default user).
"""
from __future__ import annotations

from fastapi.testclient import TestClient
from app.main import app


def test_ws_connects_without_token():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "ping"})
        response = ws.receive_json()
        assert response == {"type": "pong"}

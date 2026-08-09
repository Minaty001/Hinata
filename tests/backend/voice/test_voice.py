"""
Tests for Hinata Voice Interaction services.

Verifies STT transcription endpoint, TTS speech synthesis endpoint, and the
unified voice chat loop endpoint.
"""
from __future__ import annotations

import base64
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from httpx import AsyncClient
from tests.backend.conftest import create_test_account


async def _login(client: AsyncClient, username: str) -> str:
    await create_test_account(username)
    response = await client.post("/api/v1/auth/login", json={"username": username, "password": "password123"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_transcribe_audio(client: AsyncClient):
    token = await _login(client, "voice_user_1")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Setup mock audio bytes
    audio_bytes = b"RIFFmockaudiobytesdata"
    
    with patch("app.api.voice.transcriber.transcribe", new_callable=AsyncMock) as mock_transcribe:
        mock_transcribe.return_value = "Hello Hinata companion"
        
        response = await client.post(
            "/api/v1/voice/transcribe",
            headers=headers,
            files={"file": ("test.wav", audio_bytes, "audio/wav")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Hello Hinata companion"
    mock_transcribe.assert_called_once()


@pytest.mark.asyncio
async def test_synthesize_text(client: AsyncClient):
    token = await _login(client, "voice_user_2")
    headers = {"Authorization": f"Bearer {token}"}
    
    text_to_speak = "I will keep you company forever"
    
    with patch("app.api.voice.synthesizer.synthesize", new_callable=AsyncMock) as mock_synthesize:
        # Mock returns a fake PCM WAV container
        fake_wav = b"RIFFfmt data0000"
        mock_synthesize.return_value = fake_wav
        
        response = await client.post(
            "/api/v1/voice/synthesize",
            headers=headers,
            json={"text": text_to_speak}
        )
        
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content == fake_wav
    mock_synthesize.assert_called_once_with(text_to_speak, None)


@pytest.mark.asyncio
async def test_voice_chat_integration(client: AsyncClient):
    token = await _login(client, "voice_user_3")
    headers = {"Authorization": f"Bearer {token}"}
    
    audio_bytes = b"RIFFmockaudiobytesdata"
    
    with patch("app.api.voice.transcriber.transcribe", new_callable=AsyncMock) as mock_transcribe, \
         patch("app.api.voice.brain.handle", new_callable=AsyncMock) as mock_brain, \
         patch("app.api.voice.synthesizer.synthesize", new_callable=AsyncMock) as mock_synthesize:
         
        mock_transcribe.return_value = "hello hinata"
        
        # Mock brain result
        mock_result = MagicMock()
        mock_result.reply = "hello dear user"
        mock_result.chain_id = "test-chain-123"
        mock_brain.return_value = mock_result
        
        # Mock synthesise result
        fake_wav = b"RIFFfmt data1111"
        mock_synthesize.return_value = fake_wav
        
        response = await client.post(
            "/api/v1/voice/chat",
            headers=headers,
            files={"file": ("test.wav", audio_bytes, "audio/wav")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert data["transcription"] == "hello hinata"
    assert data["reply"] == "hello dear user"
    assert data["chain_id"] == "test-chain-123"
    assert "audio_base64" in data
    
    decoded_audio = base64.b64decode(data["audio_base64"])
    assert decoded_audio == fake_wav

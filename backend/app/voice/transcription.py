"""
Hinata Voice Subsystem — Speech-to-Text (STT) Transcription

Transcribes incoming user audio bytes to text messages using Groq's Whisper-large-v3.
"""
from __future__ import annotations

import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class VoiceTranscriber:
    """Handles audio transcription turn queries via Groq Whisper API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or settings.GROQ_API_KEY

    async def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "voice.wav",
        mime_type: str = "audio/wav",
    ) -> str:
        """Post audio bytes to Groq Whisper transcription API."""
        if not self.api_key or self.api_key.strip() == "":
            logger.warning("No GROQ_API_KEY found, running transcription mock fallback.")
            return "Hello companion (Mocked Transcription)"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                files = {"file": (filename, audio_bytes, mime_type)}
                data = {"model": "whisper-large-v3"}
                headers = {"Authorization": f"Bearer {self.api_key}"}
                
                res = await client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers=headers,
                    files=files,
                    data=data,
                )
                
                if res.status_code == 200:
                    result = res.json()
                    transcription = result.get("text", "").strip()
                    logger.info("Successfully transcribed audio turn: '%s'", transcription)
                    return transcription
                else:
                    logger.error(
                        "Groq Whisper STT API returned error %d: %s",
                        res.status_code,
                        res.text,
                    )
                    return "Error transcribing audio."
        except Exception as exc:
            logger.exception("Failed to connect to Groq Whisper STT endpoint")
            return "Error transcribing audio."

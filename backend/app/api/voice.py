"""
FastAPI Router for Voice Services (/api/v1/voice)

Handles voice transcription, synthesis, and unified voice chat interactions.
"""
from __future__ import annotations

import base64
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Backend imports
from app.core.security import get_current_user
from app.database.engine import get_session
from app.database.models import User
from app.core.brain import brain
from app.voice.transcription import VoiceTranscriber
from app.voice.synthesis import VoiceSynthesizer

logger = logging.getLogger(__name__)

router = APIRouter()

# Instantiate transcribers/synthesizers
transcriber = VoiceTranscriber()
synthesizer = VoiceSynthesizer()


class SynthesizeRequest(BaseModel):
    text: str
    lang: Optional[str] = None


@router.post("/transcribe")
async def post_transcribe(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Transcribe uploaded audio file to text."""
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file uploaded.")
        
    text = await transcriber.transcribe(
        audio_bytes=audio_bytes,
        filename=file.filename or "voice.wav",
        mime_type=file.content_type or "audio/wav",
    )
    return {"text": text}


@router.post("/synthesize")
async def post_synthesize(
    request: SynthesizeRequest,
    current_user: User = Depends(get_current_user),
):
    """Synthesize text reply into streaming audio bytes."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text parameter cannot be empty.")
        
    audio_bytes = await synthesizer.synthesize(request.text, request.lang)
    
    # Check format header to return appropriate mime type
    mime_type = "audio/mpeg"
    if audio_bytes.startswith(b"RIFF"):
        mime_type = "audio/wav"
        
    return Response(content=audio_bytes, media_type=mime_type)


@router.post("/chat")
async def post_voice_chat(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Unified Voice Chat endpoint.
    
    1. Transcribes incoming audio wave.
    2. Runs transcript through HinataBrain companion logic.
    3. Synthesizes brain reply to speech bytes.
    4. Returns text transcription, response text, and base64 audio data.
    """
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file uploaded.")

    # 1. Speech to Text (STT)
    transcript = await transcriber.transcribe(
        audio_bytes=audio_bytes,
        filename=file.filename or "voice.wav",
        mime_type=file.content_type or "audio/wav",
    )
    
    if not transcript or transcript == "Error transcribing audio.":
        raise HTTPException(status_code=500, detail="Could not transcribe audio message.")

    # 2. Call Core Brain handle pipeline
    brain_result = await brain.handle(
        user=current_user,
        message=transcript,
        source="voice",
        session=session,
    )
    
    # 3. Text to Speech (TTS)
    reply_audio = await synthesizer.synthesize(brain_result.reply, current_user.language)
    audio_base64 = base64.b64encode(reply_audio).decode("utf-8")
    
    mime_type = "audio/mpeg"
    if reply_audio.startswith(b"RIFF"):
        mime_type = "audio/wav"

    return {
        "transcription": transcript,
        "reply": brain_result.reply,
        "chain_id": brain_result.chain_id,
        "audio_base64": audio_base64,
        "mime_type": mime_type,
    }

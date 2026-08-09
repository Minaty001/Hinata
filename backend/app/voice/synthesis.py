"""
Hinata Voice Subsystem — Text-to-Speech (TTS) Synthesis

Synthesizes textual companion reply turns into audio speech bytes.
Supports gTTS (Google Text-to-Speech) dynamic load, falling back to clean
RIFF WAV wave generation structures if offline or dependencies are missing.
"""
from __future__ import annotations

import logging
import io
import struct
from typing import Optional

logger = logging.getLogger(__name__)


class VoiceSynthesizer:
    """Handles textual companion reply turns synthesis to audio bytes."""

    def __init__(self, default_lang: str = "en") -> None:
        self.default_lang = default_lang

    async def synthesize(self, text: str, lang: Optional[str] = None) -> bytes:
        """Synthesize text turn reply back to audio bytes (MP3/WAV)."""
        target_lang = lang or self.default_lang
        try:
            # Attempt to use standard gTTS library
            from gtts import gTTS
            
            logger.info("Synthesizing text turn speech via gTTS: '%.50s...'", text)
            fp = io.BytesIO()
            tts = gTTS(text=text, lang=target_lang, slow=False)
            tts.write_to_fp(fp)
            return fp.getvalue()
        except ImportError:
            logger.warning("gTTS not installed. Falling back to synthetic WAV format.")
            return self._generate_synthetic_wav(text)
        except Exception as exc:
            logger.exception("gTTS speech synthesis failed, falling back to WAV")
            return self._generate_synthetic_wav(text)

    def _generate_synthetic_wav(self, text: str) -> bytes:
        """Generate a valid, minimal RIFF PCM WAV audio file container with a single tone."""
        # Simple mono 8kHz 16-bit PCM sound representation (0.5s duration)
        sample_rate = 8000
        duration = 0.5
        num_samples = int(sample_rate * duration)
        
        # Write format headers
        header = bytearray(44)
        struct.pack_into("<4s", header, 0, b"RIFF")
        # Subchunk2 size is 2 bytes per sample (16-bit PCM)
        data_size = num_samples * 2
        struct.pack_into("<I", header, 4, 36 + data_size)
        struct.pack_into("<4s", header, 8, b"WAVE")
        struct.pack_into("<4s", header, 12, b"fmt ")
        struct.pack_into("<I", header, 16, 16)  # format chunk size
        struct.pack_into("<H", header, 20, 1)   # PCM format indicator
        struct.pack_into("<H", header, 22, 1)   # Mono channel
        struct.pack_into("<I", header, 24, sample_rate)
        struct.pack_into("<I", header, 28, sample_rate * 2)  # byte rate
        struct.pack_into("<H", header, 32, 2)   # block align
        struct.pack_into("<H", header, 34, 16)  # bits per sample
        struct.pack_into("<4s", header, 36, b"data")
        struct.pack_into("<I", header, 40, data_size)

        # Generate simple sine wave tone
        import math
        tone_frequency = 440.0
        data_bytes = bytearray(data_size)
        for i in range(num_samples):
            # Compute sine amplitude
            t = float(i) / sample_rate
            amplitude = int(10000.0 * math.sin(2.0 * math.pi * tone_frequency * t))
            struct.pack_into("<h", data_bytes, i * 2, amplitude)

        return bytes(header + data_bytes)

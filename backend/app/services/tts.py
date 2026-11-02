"""
Text-to-Speech (TTS) Service
Provides audio speech synthesis using Edge-TTS (local zero-cost streaming)
or Google Cloud Text-to-Speech API.
"""

import asyncio
import io
import json
import logging
import urllib.request
from typing import Optional
from ..config import settings

logger = logging.getLogger("janseva.tts")


async def synthesize_speech_edge(text: str, voice: str = "en-IN-NeerjaNeural") -> bytes:
    """Uses edge-tts to generate high quality speech asynchronously."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])
    return buffer.getvalue()


def synthesize_speech_google(text: str) -> Optional[bytes]:
    """Uses Google Cloud TTS REST API."""
    if not settings.GOOGLE_TTS_API_KEY:
        return None
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={settings.GOOGLE_TTS_API_KEY}"
    payload = {
        "input": {"text": text},
        "voice": {"languageCode": "en-IN", "name": "en-IN-Standard-A"},
        "audioConfig": {"audioEncoding": "MP3"}
    }
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=6.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            import base64
            return base64.b64decode(data["audioContent"])
    except Exception as e:
        logger.warning(f"Google Cloud TTS failed: {e}")
        return None


async def synthesize_speech(text: str) -> bytes:
    """Unified speech synthesis entry point."""
    cleaned = text[:400]
    if settings.TTS_PROVIDER == "google-cloud" and settings.GOOGLE_TTS_API_KEY:
        audio = await asyncio.to_thread(synthesize_speech_google, cleaned)
        if audio:
            return audio
    # Default to edge-tts
    try:
        return await synthesize_speech_edge(cleaned)
    except Exception as e:
        logger.error(f"Edge-TTS failed: {e}")
        # Return empty bytes or silent frame
        return b""

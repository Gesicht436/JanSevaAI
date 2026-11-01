"""
Text-to-Speech (TTS) Streaming API
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from ..services.tts import synthesize_speech

router = APIRouter()


class TTSPayload(BaseModel):
    text: str


@router.post("/tts")
async def get_speech_audio(payload: TTSPayload):
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text must not be empty.")

    audio_bytes = await synthesize_speech(payload.text)
    if not audio_bytes:
        raise HTTPException(status_code=502, detail="Speech synthesis temporarily unavailable.")

    return Response(content=audio_bytes, media_type="audio/mpeg")

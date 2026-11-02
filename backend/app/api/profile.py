"""
Profile Extraction API
Supports both natural language conversational text and raw voice audio uploads.
"""

import asyncio
from typing import Optional
import json
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from ..models.profile import CitizenProfile, ProfileExtractRequest, ProfileExtractResponse
from ..services.llm import extract_profile_with_llm, extract_profile_from_audio, merge_profiles

router = APIRouter()


MAX_AUDIO_BYTES = 4 * 1024 * 1024  # 4 MB (aligned with Vercel 4.5 MB request ceiling)
ALLOWED_AUDIO_TYPES = {"audio/webm", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg", "audio/mp4", "audio/x-m4a"}


@router.post("/profile/extract", response_model=ProfileExtractResponse)
async def extract_profile_text(req: ProfileExtractRequest):
    """Clean JSON endpoint for natural language text conversational intake."""
    raw_text = req.text or req.transcript or ""
    return await asyncio.to_thread(extract_profile_with_llm, raw_text, req.existing_profile)


@router.post("/profile/extract-audio", response_model=ProfileExtractResponse)
async def extract_profile_audio(
    audio: UploadFile = File(...),
    existing_profile_json: Optional[str] = Form(None)
):
    """Multipart endpoint for raw audio recording uploads with 4MB bounding."""
    chunk = await audio.read(MAX_AUDIO_BYTES + 1)
    if len(chunk) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio file exceeds maximum size limit of 4MB.")
    if not chunk:
        raise HTTPException(status_code=400, detail="Empty audio payload.")

    mime_type = audio.content_type or "audio/webm"
    if mime_type.lower() not in ALLOWED_AUDIO_TYPES and not mime_type.startswith("audio/"):
        raise HTTPException(status_code=415, detail=f"Unsupported audio media type: {mime_type}")

    res = await asyncio.to_thread(extract_profile_from_audio, chunk, mime_type)
    if existing_profile_json:
        try:
            exist_dict = json.loads(existing_profile_json)
            res.profile = merge_profiles(CitizenProfile(**exist_dict), res.profile)
        except Exception:
            pass
    return res

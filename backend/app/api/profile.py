"""
Profile Extraction API
Supports both natural language conversational text and raw voice audio uploads.
"""

from typing import Optional
import json
from fastapi import APIRouter, File, Form, UploadFile
from ..models.profile import CitizenProfile, ProfileExtractRequest, ProfileExtractResponse
from ..services.llm import extract_profile_with_llm, extract_profile_from_audio, merge_profiles

router = APIRouter()


@router.post("/profile/extract", response_model=ProfileExtractResponse)
async def extract_profile_text(req: ProfileExtractRequest):
    """Clean JSON endpoint for natural language text conversational intake."""
    raw_text = req.text or req.transcript or ""
    return extract_profile_with_llm(raw_text, req.existing_profile)


@router.post("/profile/extract-audio", response_model=ProfileExtractResponse)
async def extract_profile_audio(
    audio: UploadFile = File(...),
    existing_profile_json: Optional[str] = Form(None)
):
    """Multipart endpoint for raw audio recording uploads."""
    audio_bytes = await audio.read()
    mime_type = audio.content_type or "audio/webm"
    res = extract_profile_from_audio(audio_bytes, mime_type)
    if existing_profile_json:
        try:
            exist_dict = json.loads(existing_profile_json)
            res.profile = merge_profiles(CitizenProfile(**exist_dict), res.profile)
        except Exception:
            pass
    return res

"""
tts_routes.py — ElevenLabs text-to-speech for Theodore's child voice.

Endpoint:
  POST /api/tts   — Convert text to audio using Theodore's ElevenLabs voice
"""

import os
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/api/tts", tags=["tts"])

VOICE_ID = "NwINhsyo77xkEB8vHO6q"  # Theodore's voice
ELEVENLABS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"


class TTSRequest(BaseModel):
    text: str


@router.post("")
def speak(req: TTSRequest):
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise HTTPException(status_code=503, detail="TTS not configured")

    # Trim text to 500 chars max to stay within free tier limits
    text = req.text.strip()[:500]

    headers = {
        "xi-api-key": key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text,
        "model_id": "eleven_turbo_v2",   # fastest model — lowest latency
        "voice_settings": {
            "stability":        0.68,
            "similarity_boost": 0.75,
            "style":            0.12,
            "use_speaker_boost": True,
        },
    }

    try:
        resp = requests.post(ELEVENLABS_URL, headers=headers, json=body, timeout=15, stream=True)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"TTS error: {str(e)}")

    return StreamingResponse(
        resp.iter_content(chunk_size=4096),
        media_type="audio/mpeg",
        headers={"Cache-Control": "no-store"},
    )

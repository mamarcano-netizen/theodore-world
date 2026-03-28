"""
tts_routes.py — ElevenLabs text-to-speech for Theodore's child voice.

Endpoint:
  POST /api/tts   — Convert text to audio using Theodore's ElevenLabs voice
"""

import os
import re
import logging
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


def clean_for_speech(text: str) -> str:
    """Strip markdown and symbols that sound bad when spoken aloud."""
    # Remove emojis
    text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF]', '', text)
    # Remove markdown bold/italic
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)
    # Remove markdown headers (# ## ###)
    text = re.sub(r'#+\s*', '', text)
    # Remove markdown links [text](url)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove backticks
    text = re.sub(r'`+', '', text)
    # Remove bullet points and dashes at line start
    text = re.sub(r'^\s*[-•*]\s+', '', text, flags=re.MULTILINE)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Replace multiple newlines with a pause (period + space)
    text = re.sub(r'\n{2,}', '. ', text)
    # Replace single newlines with a space
    text = re.sub(r'\n', ' ', text)
    # Remove leftover hashtags
    text = re.sub(r'#\S*', '', text)
    # Clean up extra spaces
    text = re.sub(r' {2,}', ' ', text).strip()
    return text

router = APIRouter(prefix="/api/tts", tags=["tts"])

VOICE_ID = "NwINhsyo77xkEB8vHO6q"  # Theodore's custom voice
ELEVENLABS_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

logger = logging.getLogger(__name__)


class TTSRequest(BaseModel):
    text: str


@router.post("")
def speak(req: TTSRequest):
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="TTS not configured — ELEVENLABS_API_KEY missing")

    logger.warning(f"TTS called — key present: {bool(key)}, key prefix: {key[:8]}...")

    text = clean_for_speech(req.text)[:500]

    headers = {
        "xi-api-key": key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability":        0.68,
            "similarity_boost": 0.75,
        },
    }

    try:
        resp = requests.post(ELEVENLABS_URL, headers=headers, json=body, timeout=20)
        if not resp.ok:
            error_body = resp.text[:500]
            logger.error(f"ElevenLabs {resp.status_code}: {error_body}")
            raise HTTPException(status_code=502, detail=f"ElevenLabs {resp.status_code}: {error_body}")
        return StreamingResponse(
            iter([resp.content]),
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-store"},
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"TTS connection error: {e}")
        raise HTTPException(status_code=502, detail=f"TTS connection error: {str(e)}")

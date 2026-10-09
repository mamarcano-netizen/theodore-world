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
    """Strip ALL markdown and non-speech symbols before sending to TTS."""
    # Remove emojis and non-latin unicode
    text = re.sub(r'[^\x00-\x7F\u00C0-\u024F]', '', text)
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove markdown links — keep the label
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove markdown headers
    text = re.sub(r'#+\s*', '', text)
    # Remove bold and italic (any combo of * and _)
    text = re.sub(r'[\*_]{1,3}', '', text)
    # Remove backticks and code blocks
    text = re.sub(r'`+', '', text)
    # Remove bullet/list markers at line start
    text = re.sub(r'^\s*[-•>\*\d+\.]\s+', '', text, flags=re.MULTILINE)
    # Remove standalone special chars that get read aloud
    text = re.sub(r'[#&|<>~^\\]', '', text)
    # Replace multiple newlines with a natural pause
    text = re.sub(r'\n{2,}', '. ', text)
    text = re.sub(r'\n', ' ', text)
    # Collapse extra spaces
    text = re.sub(r' {2,}', ' ', text).strip()
    return text

router = APIRouter(prefix="/api/tts", tags=["tts"])

# Named voices. Anything not in here falls back to Theo, so existing callers
# that send no voice keep working exactly as before.
VOICES = {
    "theo": "NwINhsyo77xkEB8vHO6q",  # Theodore's custom child voice
    "gigi": "lrS79WFEmhRNou58slKI",  # Gigi Glow, Margarita's brand mascot
}
DEFAULT_VOICE = "theo"

VOICE_ID = VOICES[DEFAULT_VOICE]  # kept for backwards compatibility

logger = logging.getLogger(__name__)


class TTSRequest(BaseModel):
    text: str
    voice: str | None = None  # "theo" (default) or "gigi"


@router.post("")
def speak(req: TTSRequest):
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="TTS not configured — ELEVENLABS_API_KEY missing")

    voice_name = (req.voice or DEFAULT_VOICE).strip().lower()
    if voice_name not in VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown voice '{voice_name}'. Choose one of: {', '.join(VOICES)}",
        )
    voice_id = VOICES[voice_name]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    logger.warning(f"TTS called — voice: {voice_name}, key present: {bool(key)}")

    text = clean_for_speech(req.text)[:500]

    headers = {
        "xi-api-key": key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    body = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {
            "stability":        0.68,
            "similarity_boost": 0.75,
        },
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=20)
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

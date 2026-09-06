from pydantic import BaseModel
from typing import Optional


class SynthesisResponse(BaseModel):
    """Standardized TTS Response"""
    audio_url: str
    engine: str
    message: str
    emotion: Optional[str] = None

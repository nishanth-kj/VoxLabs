from pydantic import BaseModel
from typing import Optional

class TTSRequest(BaseModel):
    """Legacy/Emotional TTS Request"""
    text: str
    engine: str = "emotional"
    voice_id: Optional[str] = None
    language: str = "en"
    emotion: str = "neutral"
    speed: float = 1.0
    pitch: float = 1.0
    energy: float = 1.0

class EdgeTTSRequest(BaseModel):
    """Microsoft Edge TTS Request"""
    text: str
    voice: str
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"

class SynthesisResponse(BaseModel):
    """Standardized TTS Response"""
    audio_url: str
    engine: str
    message: str
    emotion: Optional[str] = None

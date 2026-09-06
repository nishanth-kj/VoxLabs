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

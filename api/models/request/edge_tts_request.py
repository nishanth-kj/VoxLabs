from pydantic import BaseModel


class EdgeTTSRequest(BaseModel):
    """Microsoft Edge TTS Request"""
    text: str
    voice: str
    rate: str = "+0%"
    pitch: str = "+0Hz"
    volume: str = "+0%"

from typing import Dict, List
from services.voice_service import get_voice_engine
from services.tts_service import EmotionalTTSEngine

class SystemService:
    def __init__(self):
        self.voice_engine = get_voice_engine()
        self.emotional_engine = EmotionalTTSEngine()

    def get_status(self) -> Dict:
        """Return the current health and status of the API."""
        return {
            "status": "healthy",
            "voice_engine": "advanced",
            "registered_voices": len(self.voice_engine.list_voices()),
            "engines": ["emotional", "clone", "basic", "edge"]
        }

    def get_emotions(self) -> Dict:
        """Return the dictionary of available emotions."""
        return {
            "emotions": self.emotional_engine.get_emotions(),
            "count": len(self.emotional_engine.get_emotions())
        }

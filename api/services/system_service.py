from typing import Any
from services.voice_service import get_voice_engine
from services.tts_service import EmotionalTTSEngine
from utils.logger import get_recent_logs, logger

class SystemService:
    def __init__(self):
        try:
            self.voice_engine = get_voice_engine()
            self.emotional_engine = EmotionalTTSEngine()
            logger.info("SystemService initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing SystemService: {e}")
            raise

    def get_status(self) -> dict:
        """Get current system status and engine readiness"""
        try:
            logger.info("Fetching system status...")
            status_data = {
                "engine_ready": True,
                "version": "2.1.0",
                "capabilities": ["emotional_tts", "voice_cloning", "edge_tts"],
                "memory_optimization": "enabled"
            }
            logger.debug(f"System status: {status_data}")
            return status_data
        except Exception as e:
            logger.error(f"Error fetching system status: {str(e)}", exc_info=True)
            raise

    def get_emotions(self) -> dict:
        """Get available emotional presets from the engine"""
        try:
            logger.info("Fetching available emotions...")
            emotions = self.emotional_engine.get_emotions()
            logger.debug(f"Retrieved {len(emotions)} emotions")
            return {"emotions": emotions}
        except Exception as e:
            logger.error(f"Error fetching emotions: {str(e)}", exc_info=True)
            raise

    def get_logs(self, limit: int = 200) -> dict[str, Any]:
        """Return recent in-memory backend log records for the Studio panel."""
        clamped = max(1, min(limit, 500))
        logs = get_recent_logs(clamped)
        return {"logs": logs, "count": len(logs)}

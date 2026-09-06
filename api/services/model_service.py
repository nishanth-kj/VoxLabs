import asyncio
import shutil
from typing import Any

from constants.model_kind import ModelKind, ModelProvider
from services.edge_tts_service import EdgeTTSService
from utils.logger import logger


class ModelService:
    """Catalog of synthesis engines and remote voice models available to Studio."""

    def __init__(self):
        self.edge = EdgeTTSService()

    def _engine_catalog(self, edge_voice_count: int, edge_available: bool) -> list[dict[str, Any]]:
        ffmpeg = bool(shutil.which("ffmpeg"))
        return [
            {
                "id": "emotional",
                "name": "Emotional TTS",
                "kind": ModelKind.ENGINE.value,
                "provider": ModelProvider.LOCAL.value,
                "status": "available" if ffmpeg else "degraded",
                "offline": True,
                "description": "Local gTTS synthesis with librosa emotion, speed, pitch, and energy.",
                "capabilities": ["emotion", "speed", "pitch", "energy"],
                "endpoint": "/api/tts",
                "note": None if ffmpeg else "FFmpeg is not on PATH. Audio export may fail.",
            },
            {
                "id": "clone",
                "name": "Voice cloning",
                "kind": ModelKind.ENGINE.value,
                "provider": ModelProvider.LOCAL.value,
                "status": "available",
                "offline": True,
                "description": "Consent-based local cloning from an audio sample or a design prompt.",
                "capabilities": ["consent", "register", "design", "revoke"],
                "endpoint": "/api/voices",
                "note": None,
            },
            {
                "id": "edge",
                "name": "Microsoft Edge TTS",
                "kind": ModelKind.ENGINE.value,
                "provider": ModelProvider.MICROSOFT.value,
                "status": "available" if edge_available else "unavailable",
                "offline": False,
                "description": "Neural voices from Microsoft Edge TTS. Processed through this machine.",
                "capabilities": ["rate", "pitch", "volume", "locales"],
                "endpoint": "/api/tts/edge/generate",
                "note": None if edge_available else "Could not reach Edge TTS voice list.",
                "variant_count": edge_voice_count,
            },
        ]

    async def list_models(self) -> dict[str, Any]:
        logger.info("Listing available models")
        edge_voices: list[dict[str, Any]] = []
        edge_available = False
        try:
            edge_voices = await asyncio.wait_for(self.edge.get_voices(), timeout=8)
            edge_available = True
        except Exception as exc:
            logger.warning(f"Edge TTS voices unavailable: {exc}")

        engines = self._engine_catalog(len(edge_voices), edge_available)
        voices = [
            {
                "id": voice["ShortName"],
                "name": voice.get("FriendlyName") or voice["ShortName"],
                "kind": ModelKind.VOICE.value,
                "provider": ModelProvider.MICROSOFT.value,
                "status": "available",
                "offline": False,
                "locale": voice.get("Locale"),
                "gender": voice.get("Gender"),
                "engine": "edge",
            }
            for voice in edge_voices
        ]
        models = engines + voices
        return {
            "models": models,
            "engines": engines,
            "voices": voices,
            "count": len(models),
            "engine_count": len(engines),
            "voice_count": len(voices),
        }

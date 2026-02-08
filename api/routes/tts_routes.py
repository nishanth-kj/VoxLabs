from fastapi import APIRouter, Form
from typing import Optional
from services.edge_tts_service import EdgeTTSService
from services.voice_service import get_voice_engine
from pathlib import Path
from models import EdgeTTSRequest, TTSRequest
from utils.response_handler import ApiResponse
from utils.logger import logger

class TTSRoutes:
    def __init__(self):
        self.router = APIRouter(prefix="/api/tts", tags=["TTS"])
        self.edge_service = EdgeTTSService()
        self.voice_engine = get_voice_engine()
        self.audio_dir = Path("static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.router.add_api_route("/edge/voices", self.list_edge_voices, methods=["GET"])
        self.router.add_api_route("/edge/generate", self.generate_edge_speech, methods=["POST"])
        self.router.add_api_route("", self.text_to_speech, methods=["POST"])

    async def list_edge_voices(self):
        """List all available Edge TTS voices."""
        try:
            logger.info("GET /api/tts/edge/voices - Listing Edge voices")
            voices = await self.edge_service.get_voices()
            return ApiResponse(data=voices).success()
        except Exception as e:
            logger.error(f"Error in list_edge_voices: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

    async def generate_edge_speech(self, request: EdgeTTSRequest):
        """Generate speech using Edge TTS and return a URL."""
        try:
            logger.info(f"POST /api/tts/edge/generate - Edge speech requested for text: {request.text[:30]}...")
            audio_data = await self.edge_service.generate_speech(
                text=request.text,
                voice=request.voice,
                rate=request.rate,
                pitch=request.pitch,
                volume=request.volume
            )
            
            filename = f"edge_{hash(request.text)}_{request.voice.split('-')[-1]}.mp3"
            filepath = self.audio_dir / filename
            with open(filepath, "wb") as f:
                f.write(audio_data)
            
            logger.debug(f"Edge audio file saved: {filepath}")
            data = {
                "audio_url": f"/static/audio/{filename}",
                "engine": "edge",
                "message": "Edge speech generated successfully"
            }
            logger.info("Edge speech generation successful")
            return ApiResponse(data=data).success()
        except Exception as e:
            logger.error(f"Error in generate_edge_speech: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

    async def text_to_speech(
        self,
        text: str = Form(...),
        engine: str = Form("emotional"),
        voice_id: Optional[str] = Form(None),
        language: str = Form("en"),
        emotion: str = Form("neutral"),
        speed: float = Form(1.0),
        pitch: float = Form(1.0),
        energy: float = Form(1.0)
    ):
        """Generate speech from text using the advanced/emotional engine."""
        try:
            logger.info(f"POST /api/tts - TTS requested (engine={engine}, emotion={emotion})")
            audio_data = self.voice_engine.synthesize(
                text=text,
                engine=engine,
                voice_id=voice_id,
                language=language,
                emotion=emotion,
                speed=speed,
                pitch=pitch,
                energy=energy
            )
            
            filename = f"tts_{hash(text)}_{emotion}.mp3"
            filepath = self.audio_dir / filename
            with open(filepath, "wb") as f:
                f.write(audio_data)
            
            logger.debug(f"TTS audio file saved: {filepath}")
            data = {
                "audio_url": f"/static/audio/{filename}",
                "engine": engine,
                "emotion": emotion if engine == "emotional" else None,
                "message": "Speech generated successfully"
            }
            logger.info("TTS generation successful")
            return ApiResponse(data=data).success()
        except Exception as e:
            logger.error(f"Error in text_to_speech endpoint: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

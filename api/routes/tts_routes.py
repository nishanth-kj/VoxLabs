from fastapi import APIRouter, Depends, Form
from typing import Annotated

from services.edge_tts_service import EdgeTTSService
from services.voice_service import VoiceEngine, get_voice_engine
from models import EdgeTTSRequest, TTSRequest, APIResponse
from utils.response_handler import ApiResponse
from utils.logger import logger

router = APIRouter(prefix="/api/tts", tags=["TTS"])


def get_edge_tts_service() -> EdgeTTSService:
    return EdgeTTSService()


@router.get("/edge/voices", response_model=APIResponse)
async def list_edge_voices(edge_service: EdgeTTSService = Depends(get_edge_tts_service)):
    """List all available Edge TTS voices."""
    logger.info("GET /api/tts/edge/voices - Listing Edge voices")
    voices = await edge_service.get_voices()
    return ApiResponse(data=voices).success()


@router.post("/edge/generate", response_model=APIResponse)
async def generate_edge_speech(
    request: EdgeTTSRequest,
    edge_service: EdgeTTSService = Depends(get_edge_tts_service),
):
    """Generate speech using Edge TTS and return a URL."""
    logger.info(f"POST /api/tts/edge/generate - Edge speech requested for text: {request.text[:30]}...")
    data = await edge_service.generate_and_save(
        text=request.text,
        voice=request.voice,
        rate=request.rate,
        pitch=request.pitch,
        volume=request.volume,
    )
    return ApiResponse(data=data).success()


@router.post("", response_model=APIResponse)
async def text_to_speech(
    request: Annotated[TTSRequest, Form()],
    voice_engine: VoiceEngine = Depends(get_voice_engine),
):
    """Generate speech from text using the advanced/emotional engine."""
    logger.info(f"POST /api/tts - TTS requested (engine={request.engine}, emotion={request.emotion})")
    data = voice_engine.synthesize_and_save(
        text=request.text,
        engine=request.engine,
        voice_id=request.voice_id,
        language=request.language,
        emotion=request.emotion,
        speed=request.speed,
        pitch=request.pitch,
        energy=request.energy,
    )
    return ApiResponse(data=data).success()

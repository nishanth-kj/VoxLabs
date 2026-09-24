from fastapi import APIRouter

from app.models.request import RegenerateRequest, TTSRequest
from app.models.response import ApiResponse
from app.services.tts_service import tts_service

router = APIRouter(prefix="/api/tts", tags=["TTS"])


@router.post("")
def generate(body: TTSRequest) -> ApiResponse:
    data = {"job": tts_service.generate_async(body)} if body.background else tts_service.generate(body)
    return ApiResponse(data).success()


@router.post("/regenerate")
def regenerate(body: RegenerateRequest) -> ApiResponse:
    data = tts_service.regenerate(body)
    return ApiResponse(data).success()

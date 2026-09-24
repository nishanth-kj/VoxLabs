from fastapi import APIRouter

from app.models.request import RegenerateRequest, TTSRequest
from app.models.response import ApiResponse
from app.services.tts_service import tts_service

router = APIRouter(prefix="/api/tts", tags=["TTS"])


@router.post("")
def generate(body: TTSRequest) -> ApiResponse:
    params = body.model_dump(exclude={"text", "background"})
    if body.background:
        return ApiResponse.success({"job": tts_service.generate_async(body.text, **params)})
    return ApiResponse.success(tts_service.generate(body.text, **params))


@router.post("/regenerate")
def regenerate(body: RegenerateRequest) -> ApiResponse:
    return ApiResponse.success(tts_service.regenerate(body.audios_id, seed=body.seed))

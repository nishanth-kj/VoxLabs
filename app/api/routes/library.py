from fastapi import APIRouter

from app.models.response import ApiResponse
from app.services.audio_service import audio_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/library", tags=["Library"])


@router.get("")
def list_library(kind: str | None = None, limit: int = 1000) -> ApiResponse:
    """Everything VoxLabs keeps, newest first: generated, imported, processed and rendered audio, exported files
    and voice samples. `kind` keeps one of them; each item says whether its file still `exists`."""
    limit = Validation.limit(limit)
    data = audio_service.library(kind or None, limit)
    return ApiResponse(data).success()

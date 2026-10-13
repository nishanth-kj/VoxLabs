from fastapi import APIRouter

from app.models.request import ExportRequest
from app.models.response import ApiResponse
from app.services.audio_service import audio_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/exports", tags=["Exports"])


@router.get("")
def list_exports(limit: int = 500) -> ApiResponse:
    """Every exported file, newest first, with `exists` telling whether it is still where it was saved."""
    limit = Validation.limit(limit)
    data = audio_service.list_exports(limit)
    return ApiResponse(data).success()


@router.post("")
def save_export(body: ExportRequest) -> ApiResponse:
    """No id: export `audios_id` and record it. Id + status Deleted: remove it from the list (`delete_file` too)."""
    data = audio_service.save_export(body)
    return ApiResponse(data).success()

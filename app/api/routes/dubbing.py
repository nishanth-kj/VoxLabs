from fastapi import APIRouter

from app.models.request import (
    DubbingImportRequest,
    DubbingProjectRequest,
    DubbingRenderRequest,
    DubbingSegmentRequest,
)
from app.models.response import ApiResponse
from app.services.dubbing_service import dubbing_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/dubbing", tags=["Dubbing"])


@router.get("")
def list_dubbing_projects() -> ApiResponse:
    data = dubbing_service.list_projects()
    return ApiResponse(data).success()


@router.get("/{dubbing_projects_id}")
def get_dubbing_project(dubbing_projects_id: int) -> ApiResponse:
    dubbing_projects_id = Validation.require_id(dubbing_projects_id, "dubbing_projects_id")
    data = dubbing_service.get(dubbing_projects_id)
    return ApiResponse(data).success()


@router.post("")
def save_dubbing_project(body: DubbingProjectRequest) -> ApiResponse:
    """Create (no dubbing_projects_id), update (dubbing_projects_id) or delete (status Deleted)."""
    data = dubbing_service.save(body)
    return ApiResponse(data).success()


@router.post("/import-subtitles")
def import_subtitles(body: DubbingImportRequest) -> ApiResponse:
    data = dubbing_service.import_subtitles(
        dubbing_projects_id=body.dubbing_projects_id,
        content=body.content,
        format=body.format,
        replace_existing=body.replace_existing,
    )
    return ApiResponse(data).success()


@router.get("/{dubbing_projects_id}/subtitles")
def export_subtitles(dubbing_projects_id: int, format: str = "srt", use_target: bool = True) -> ApiResponse:
    dubbing_projects_id = Validation.require_id(dubbing_projects_id, "dubbing_projects_id")
    data = dubbing_service.export_subtitles(dubbing_projects_id, format=format, use_target=use_target)
    return ApiResponse(data).success()


@router.post("/segments")
def save_segment(body: DubbingSegmentRequest) -> ApiResponse:
    data = dubbing_service.save_segment(body)
    return ApiResponse(data).success()


@router.post("/segments/{dubbing_segments_id}/generate")
def generate_segment(dubbing_segments_id: int) -> ApiResponse:
    dubbing_segments_id = Validation.require_id(dubbing_segments_id, "dubbing_segments_id")
    data = dubbing_service.generate_segment(dubbing_segments_id)
    return ApiResponse(data).success()


@router.post("/{dubbing_projects_id}/auto-map")
def auto_map_speakers(dubbing_projects_id: int) -> ApiResponse:
    dubbing_projects_id = Validation.require_id(dubbing_projects_id, "dubbing_projects_id")
    data = dubbing_service.auto_map_speakers(dubbing_projects_id)
    return ApiResponse(data).success()


@router.post("/{dubbing_projects_id}/generate-all")
def generate_all(dubbing_projects_id: int, overwrite_existing: bool = False) -> ApiResponse:
    dubbing_projects_id = Validation.require_id(dubbing_projects_id, "dubbing_projects_id")
    data = dubbing_service.generate_all(dubbing_projects_id, overwrite_existing=overwrite_existing)
    return ApiResponse(data).success()


@router.post("/render")
def render_video(body: DubbingRenderRequest) -> ApiResponse:
    data = dubbing_service.render_video(body)
    return ApiResponse(data).success()


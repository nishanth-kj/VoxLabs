from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form
from fastapi.responses import FileResponse

from app.models.request import AudioExportRequest, AudioImportRequest, AudioProcessRequest
from app.models.response import ApiResponse
from app.services.audio_service import audio_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/audio", tags=["Audio"])


@router.get("")
def list_audio(projects_id: int | None = None, limit: int = 100) -> ApiResponse:
    projects_id = Validation.optional_id(projects_id, "projects_id")
    limit = Validation.limit(limit)
    data = audio_service.list_audios(projects_id, limit)
    return ApiResponse(data).success()


@router.get("/{audio_id}")
def get_audio(audio_id: int) -> ApiResponse:
    audio_id = Validation.require_id(audio_id, "audios_id")
    data = audio_service.get(audio_id)
    return ApiResponse(data).success()


@router.get("/{audio_id}/file")
def download_audio(audio_id: int) -> FileResponse:
    audio_id = Validation.require_id(audio_id, "audios_id")
    audio = audio_service.get(audio_id)
    return FileResponse(audio["path"], filename=Path(audio["path"]).name)


@router.post("/import")
def import_audio(body: Annotated[AudioImportRequest, Form()]) -> ApiResponse:
    data = audio_service.import_upload(body)
    return ApiResponse(data).success()


@router.post("/process")
def process_audio(body: AudioProcessRequest) -> ApiResponse:
    """Enhance with `steps`/`preset`, or render an edit list with `ops`."""
    data = {"job": audio_service.process_async(body)} if body.background else audio_service.process(body)
    return ApiResponse(data).success()


@router.post("/export")
def export_audio(body: AudioExportRequest) -> FileResponse:
    path = audio_service.export(body)
    return FileResponse(path, filename=Path(path).name)

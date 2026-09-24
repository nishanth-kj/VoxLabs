from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.api.routes import save_upload
from app.models.request import AudioExportRequest, AudioProcessRequest
from app.models.response import ApiResponse
from app.services.audio_service import audio_service
from app.utils.files import remove_file, subdir, unique_path

router = APIRouter(prefix="/api/audio", tags=["Audio"])


@router.get("")
def list_audio(projects_id: int | None = None, limit: int = 100) -> ApiResponse:
    return ApiResponse.success(audio_service.list_audios(projects_id, limit))


@router.get("/{audio_id}")
def get_audio(audio_id: int) -> ApiResponse:
    return ApiResponse.success(audio_service.get(audio_id))


@router.get("/{audio_id}/file")
def download_audio(audio_id: int):
    audio = audio_service.get(audio_id)
    return FileResponse(audio["path"], filename=Path(audio["path"]).name)


@router.post("/import")
def import_audio(file: UploadFile = File(...), projects_id: int | None = Form(None)) -> ApiResponse:
    path = save_upload(file)
    try:
        return ApiResponse.success(audio_service.import_file(path, projects_id, Path(file.filename or "audio").stem))
    finally:
        remove_file(path)


@router.post("/process")
def process_audio(body: AudioProcessRequest) -> ApiResponse:
    if body.background:
        return ApiResponse.success({"job": audio_service.process_async(body.audios_id, body.steps, body.preset,
                                                                       body.ops)})
    if body.ops is not None:
        return ApiResponse.success(audio_service.render_edits(body.audios_id, body.ops))
    return ApiResponse.success(audio_service.process(body.audios_id, body.steps, body.preset))


@router.post("/export")
def export_audio(body: AudioExportRequest):
    audio = audio_service.get(body.audios_id)
    dest = unique_path(subdir("exports"), audio["name"], body.format)
    path = audio_service.export(body.audios_id, dest, body.format, body.sample_rate)
    return FileResponse(path, filename=Path(path).name)

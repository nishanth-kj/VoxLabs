from fastapi import APIRouter, File, UploadFile

from app.api.routes import save_upload
from app.models.request import VoiceRequest
from app.models.response import ApiResponse
from app.services.voice_service import voice_service
from app.utils.files import remove_file

router = APIRouter(prefix="/api/voices", tags=["Voices"])


@router.get("")
def list_voices(include_revoked: bool = False, users_id: int | None = None) -> ApiResponse:
    return ApiResponse.success(voice_service.list_voices(include_revoked=include_revoked, users_id=users_id))


@router.get("/{voice_id}")
def get_voice(voice_id: int) -> ApiResponse:
    return ApiResponse.success(voice_service.get(voice_id))


@router.post("")
def save_voice(body: VoiceRequest) -> ApiResponse:
    """Create a preset voice (no voices_id), update (voices_id) or delete (voices_id + status Deleted)."""
    return ApiResponse.success(voice_service.save(**body.model_dump(exclude_unset=True)))


@router.post("/{voice_id}/revoke")
def revoke_voice(voice_id: int) -> ApiResponse:
    return ApiResponse.success(voice_service.revoke(voice_id))


@router.get("/{voice_id}/export")
def export_voice(voice_id: int) -> ApiResponse:
    return ApiResponse.success(voice_service.export_metadata(voice_id))


@router.post("/{voice_id}/samples")
def add_sample(voice_id: int, audio: UploadFile = File(...)) -> ApiResponse:
    path = save_upload(audio)
    try:
        return ApiResponse.success(voice_service.attach_sample(voice_id, path))
    finally:
        remove_file(path)


@router.post("/samples/{sample_id}/remove")
def remove_sample(sample_id: int) -> ApiResponse:
    return ApiResponse.success(voice_service.remove_sample(sample_id))

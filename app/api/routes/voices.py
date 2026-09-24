from fastapi import APIRouter, File, UploadFile

from app.models.request import VoiceRequest
from app.models.response import ApiResponse
from app.services.voice_service import voice_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/voices", tags=["Voices"])


@router.get("")
def list_voices(include_revoked: bool = False, users_id: int | None = None) -> ApiResponse:
    users_id = Validation.optional_id(users_id, "users_id")
    data = voice_service.list_voices(include_revoked=include_revoked, users_id=users_id)
    return ApiResponse(data).success()


@router.get("/{voice_id}")
def get_voice(voice_id: int) -> ApiResponse:
    voice_id = Validation.require_id(voice_id, "voices_id")
    data = voice_service.get(voice_id)
    return ApiResponse(data).success()


@router.post("")
def save_voice(body: VoiceRequest) -> ApiResponse:
    """Create a preset voice (no voices_id), update (voices_id) or delete (voices_id + status Deleted)."""
    data = voice_service.save(body)
    return ApiResponse(data).success()


@router.post("/{voice_id}/revoke")
def revoke_voice(voice_id: int) -> ApiResponse:
    voice_id = Validation.require_id(voice_id, "voices_id")
    data = voice_service.revoke(voice_id)
    return ApiResponse(data).success()


@router.get("/{voice_id}/export")
def export_voice(voice_id: int) -> ApiResponse:
    voice_id = Validation.require_id(voice_id, "voices_id")
    data = voice_service.export_metadata(voice_id)
    return ApiResponse(data).success()


@router.post("/{voice_id}/samples")
def add_sample(voice_id: int, audio: UploadFile = File(...)) -> ApiResponse:
    voice_id = Validation.require_id(voice_id, "voices_id")
    data = voice_service.attach_upload(voice_id, audio)
    return ApiResponse(data).success()


@router.post("/samples/{sample_id}/remove")
def remove_sample(sample_id: int) -> ApiResponse:
    sample_id = Validation.require_id(sample_id, "voice_samples_id")
    data = voice_service.remove_sample(sample_id)
    return ApiResponse(data).success()

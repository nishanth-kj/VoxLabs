from fastapi import APIRouter, File, Form, UploadFile

from app.api.routes import save_upload
from app.models.response import ApiResponse
from app.services.clone_service import clone_service
from app.utils.files import remove_file

# Registered before voices.py so /api/voices/clone is not captured by /{voice_id}.
router = APIRouter(prefix="/api/voices", tags=["Voice cloning"])


@router.post("/clone")
def clone_voice(
    name: str = Form(...),
    consent: bool = Form(...),
    granted_by: str = Form(...),
    speaker_name: str = Form(...),
    statement: str = Form(""),
    language: str = Form("en"),
    description: str = Form(""),
    model_key: str | None = Form(None),
    users_id: int | None = Form(None),
    background: bool = Form(False),
    samples: list[UploadFile] = File(...),
) -> ApiResponse:
    """Clone a voice from one or more samples (multipart). Requires explicit consent."""
    consent_data = {"confirmed": consent, "granted_by": granted_by, "speaker_name": speaker_name,
                    "statement": statement}
    options = {"language": language, "description": description, "model_key": model_key, "users_id": users_id}
    paths = [save_upload(s) for s in samples]
    if background:
        job = clone_service.clone_async(paths, name, consent_data, delete_samples_after=True, **options)
        return ApiResponse.success({"job": job})
    try:
        return ApiResponse.success(clone_service.clone(paths, name, consent_data, **options))
    finally:
        for path in paths:
            remove_file(path)


@router.post("/analyze")
def analyze_sample(sample: UploadFile = File(...)) -> ApiResponse:
    path = save_upload(sample)
    try:
        return ApiResponse.success(clone_service.analyze_sample(path))
    finally:
        remove_file(path)

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.models.request import CloneRequest
from app.models.response import ApiResponse
from app.services.clone_service import clone_service

# Registered before voices.py so /api/voices/clone is not captured by /{voice_id}.
router = APIRouter(prefix="/api/voices", tags=["Voice cloning"])


@router.post("/clone")
def clone_voice(body: Annotated[CloneRequest, Form()]) -> ApiResponse:
    """Clone a voice from one or more samples (multipart form). Requires explicit consent."""
    data = clone_service.clone_upload(body)
    return ApiResponse(data).success()


@router.post("/analyze")
def analyze_sample(sample: UploadFile = File(...)) -> ApiResponse:
    data = clone_service.analyze_upload(sample)
    return ApiResponse(data).success()

from fastapi import APIRouter

from app.models.response import ApiResponse
from app.services.system_service import system_service

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health() -> ApiResponse:
    data = system_service.health()
    return ApiResponse(data).success()


@router.get("/presets")
def presets() -> ApiResponse:
    data = system_service.presets()
    return ApiResponse(data).success()

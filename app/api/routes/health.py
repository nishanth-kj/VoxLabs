from fastapi import APIRouter

from app.models.response import ApiResponse
from app.services.system_service import system_service

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health() -> ApiResponse:
    return ApiResponse.success(system_service.health())


@router.get("/presets")
def presets() -> ApiResponse:
    return ApiResponse.success(system_service.presets())

from fastapi import APIRouter

from app.models.response import ApiResponse
from app.services.model_service import model_service

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("")
def list_models(model_type: str | None = None) -> ApiResponse:
    return ApiResponse.success(model_service.list_models(model_type))


@router.get("/{model_id}")
def get_model(model_id: str) -> ApiResponse:
    return ApiResponse.success(model_service.get(model_id))


@router.post("/{model_id}/load")
def load_model(model_id: str, background: bool = False) -> ApiResponse:
    if background:
        return ApiResponse.success({"job": model_service.load_async(model_id)})
    return ApiResponse.success(model_service.load(model_id))


@router.post("/{model_id}/unload")
def unload_model(model_id: str) -> ApiResponse:
    return ApiResponse.success(model_service.unload(model_id))


@router.post("/{model_id}/install")
def install_model(model_id: str, accept_license: bool = False) -> ApiResponse:
    return ApiResponse.success({"job": model_service.install_async(model_id, accept_license)})


@router.get("/{model_id}/health")
def model_health(model_id: str) -> ApiResponse:
    return ApiResponse.success(model_service.health(model_id))

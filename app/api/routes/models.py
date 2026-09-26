from fastapi import APIRouter

from app.models.response import ApiResponse
from app.services.model_service import model_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("")
def list_models(model_type: str | None = None) -> ApiResponse:
    data = model_service.list_models(model_type)
    return ApiResponse(data).success()


@router.get("/{model_id}")
def get_model(model_id: str) -> ApiResponse:
    model_ref = Validation.require_ref(model_id, "model_id")
    data = model_service.get(model_ref)
    return ApiResponse(data).success()


@router.post("/{model_id}/load")
def load_model(model_id: str, background: bool = False) -> ApiResponse:
    model_ref = Validation.require_ref(model_id, "model_id")
    data = {"job": model_service.load_async(model_ref)} if background else model_service.load(model_ref)
    return ApiResponse(data).success()


@router.post("/{model_id}/unload")
def unload_model(model_id: str) -> ApiResponse:
    model_ref = Validation.require_ref(model_id, "model_id")
    data = model_service.unload(model_ref)
    return ApiResponse(data).success()


@router.post("/{model_id}/install")
def install_model(model_id: str, accept_license: bool = False) -> ApiResponse:
    model_ref = Validation.require_ref(model_id, "model_id")
    data = {"job": model_service.install_async(model_ref, accept_license)}
    return ApiResponse(data).success()


@router.get("/{model_id}/health")
def model_health(model_id: str) -> ApiResponse:
    model_ref = Validation.require_ref(model_id, "model_id")
    data = model_service.health(model_ref)
    return ApiResponse(data).success()

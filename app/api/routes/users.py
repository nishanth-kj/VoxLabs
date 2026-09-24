from fastapi import APIRouter

from app.models.request import UserRequest
from app.models.response import ApiResponse
from app.services.user_service import user_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("")
def list_users() -> ApiResponse:
    return ApiResponse.success(user_service.list_users())


@router.get("/{user_id}")
def get_user(user_id: int) -> ApiResponse:
    return ApiResponse.success(user_service.get_user(user_id))


@router.post("")
def save_user(body: UserRequest) -> ApiResponse:
    """Create (no users_id), update (users_id) or delete (users_id + status Deleted)."""
    return ApiResponse.success(user_service.save(**body.model_dump()))

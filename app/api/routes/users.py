from fastapi import APIRouter

from app.models.request import UserRequest
from app.models.response import ApiResponse
from app.services.user_service import user_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("")
def list_users() -> ApiResponse:
    data = user_service.list_users()
    return ApiResponse(data).success()


@router.get("/{user_id}")
def get_user(user_id: int) -> ApiResponse:
    user_id = Validation.require_id(user_id, "users_id")
    data = user_service.get_user(user_id)
    return ApiResponse(data).success()


@router.post("")
def save_user(body: UserRequest) -> ApiResponse:
    """Create (no users_id), update (users_id) or delete (users_id + status Deleted)."""
    data = user_service.save(body)
    return ApiResponse(data).success()

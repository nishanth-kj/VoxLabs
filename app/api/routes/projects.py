from fastapi import APIRouter

from app.models.request import ProjectRequest
from app.models.response import ApiResponse
from app.services.project_service import project_service

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("")
def list_projects(users_id: int | None = None) -> ApiResponse:
    return ApiResponse.success(project_service.list_projects(users_id=users_id))


@router.get("/{project_id}")
def get_project(project_id: int) -> ApiResponse:
    return ApiResponse.success(project_service.open_project(project_id))


@router.post("")
def save_project(body: ProjectRequest) -> ApiResponse:
    """Create (no projects_id), update (projects_id) or delete (projects_id + status Deleted)."""
    return ApiResponse.success(project_service.save(**body.model_dump()))


@router.post("/{project_id}/duplicate")
def duplicate_project(project_id: int) -> ApiResponse:
    return ApiResponse.success(project_service.duplicate_project(project_id))

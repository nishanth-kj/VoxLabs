from fastapi import APIRouter

from app.models.request import ProjectRequest
from app.models.response import ApiResponse
from app.services.project_service import project_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("")
def list_projects(users_id: int | None = None) -> ApiResponse:
    users_id = Validation.optional_id(users_id, "users_id")
    data = project_service.list_projects(users_id=users_id)
    return ApiResponse(data).success()


@router.get("/{project_id}")
def get_project(project_id: int) -> ApiResponse:
    project_id = Validation.require_id(project_id, "projects_id")
    data = project_service.open_project(project_id)
    return ApiResponse(data).success()


@router.post("")
def save_project(body: ProjectRequest) -> ApiResponse:
    """Create (no projects_id), update (projects_id) or delete (projects_id + status Deleted)."""
    data = project_service.save(body)
    return ApiResponse(data).success()


@router.post("/{project_id}/duplicate")
def duplicate_project(project_id: int) -> ApiResponse:
    project_id = Validation.require_id(project_id, "projects_id")
    data = project_service.duplicate_project(project_id)
    return ApiResponse(data).success()

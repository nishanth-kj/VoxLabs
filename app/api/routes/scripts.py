from fastapi import APIRouter

from app.models.request import GenerateScriptRequest, ScriptRequest, SectionRequest
from app.models.response import ApiResponse
from app.services.script_service import script_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/scripts", tags=["Scripts"])


@router.get("")
def list_scripts(projects_id: int | None = None) -> ApiResponse:
    projects_id = Validation.optional_id(projects_id, "projects_id")
    data = script_service.list_scripts(projects_id)
    return ApiResponse(data).success()


@router.get("/{script_id}")
def get_script(script_id: int) -> ApiResponse:
    script_id = Validation.require_id(script_id, "scripts_id")
    data = script_service.get(script_id)
    return ApiResponse(data).success()


@router.post("")
def save_script(body: ScriptRequest) -> ApiResponse:
    """Create (no scripts_id), update (scripts_id) or delete (scripts_id + status Deleted)."""
    data = script_service.save(body)
    return ApiResponse(data).success()


@router.post("/{script_id}/generate")
def generate_script(script_id: int, body: GenerateScriptRequest | None = None) -> ApiResponse:
    script_id = Validation.require_id(script_id, "scripts_id")
    body = body or GenerateScriptRequest()
    if body.background:
        data = {"job": script_service.generate_async(script_id, body)}
    else:
        data = script_service.generate(script_id, body)
    return ApiResponse(data).success()


@router.post("/sections")
def update_section(body: SectionRequest) -> ApiResponse:
    data = script_service.update_section(body)
    return ApiResponse(data).success()


@router.post("/sections/{section_id}/generate")
def generate_section(section_id: int, seed: int | None = None) -> ApiResponse:
    section_id = Validation.require_id(section_id, "script_sections_id")
    data = script_service.generate_section(section_id, seed)
    return ApiResponse(data).success()


@router.post("/takes/{take_id}/select")
def select_take(take_id: int) -> ApiResponse:
    take_id = Validation.require_id(take_id, "takes_id")
    data = script_service.select_take(take_id)
    return ApiResponse(data).success()

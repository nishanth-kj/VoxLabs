from fastapi import APIRouter

from app.models.request import GenerateScriptRequest, ScriptRequest, SectionRequest
from app.models.response import ApiResponse
from app.services.script_service import script_service

router = APIRouter(prefix="/api/scripts", tags=["Scripts"])


@router.get("")
def list_scripts(projects_id: int | None = None) -> ApiResponse:
    return ApiResponse.success(script_service.list_scripts(projects_id))


@router.get("/{script_id}")
def get_script(script_id: int) -> ApiResponse:
    return ApiResponse.success(script_service.get(script_id))


@router.post("")
def save_script(body: ScriptRequest) -> ApiResponse:
    """Create (no scripts_id), update (scripts_id) or delete (scripts_id + status Deleted)."""
    return ApiResponse.success(script_service.save(**body.model_dump(exclude_unset=True)))


@router.post("/{script_id}/generate")
def generate_script(script_id: int, body: GenerateScriptRequest | None = None) -> ApiResponse:
    body = body or GenerateScriptRequest()
    if body.background:
        return ApiResponse.success({"job": script_service.generate_async(script_id, body.regenerate)})
    return ApiResponse.success(script_service.generate(script_id, body.regenerate))


@router.post("/sections")
def update_section(body: SectionRequest) -> ApiResponse:
    fields = body.model_dump(exclude_unset=True)
    return ApiResponse.success(script_service.update_section(fields.pop("script_sections_id"), **fields))


@router.post("/sections/{section_id}/generate")
def generate_section(section_id: int, seed: int | None = None) -> ApiResponse:
    return ApiResponse.success(script_service.generate_section(section_id, seed))


@router.post("/takes/{take_id}/select")
def select_take(take_id: int) -> ApiResponse:
    return ApiResponse.success(script_service.select_take(take_id))

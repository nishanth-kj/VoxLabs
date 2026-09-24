from fastapi import APIRouter

from app.models.response import ApiResponse
from app.services.job_service import job_service

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.get("")
def list_jobs(active: bool = False, limit: int = 50) -> ApiResponse:
    return ApiResponse.success(job_service.list_jobs(active_only=active, limit=limit))


@router.get("/{job_id}")
def get_job(job_id: int) -> ApiResponse:
    return ApiResponse.success(job_service.get(job_id))


@router.post("/{job_id}/cancel")
def cancel_job(job_id: int) -> ApiResponse:
    return ApiResponse.success(job_service.cancel(job_id))

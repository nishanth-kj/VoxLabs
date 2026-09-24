from fastapi import APIRouter

from app.models.response import ApiResponse
from app.services.job_service import job_service
from app.utils.validation import Validation

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


@router.get("")
def list_jobs(active: bool = False, limit: int = 50) -> ApiResponse:
    limit = Validation.limit(limit)
    data = job_service.list_jobs(active_only=active, limit=limit)
    return ApiResponse(data).success()


@router.get("/{job_id}")
def get_job(job_id: int) -> ApiResponse:
    job_id = Validation.require_id(job_id, "jobs_id")
    data = job_service.get(job_id)
    return ApiResponse(data).success()


@router.post("/{job_id}/cancel")
def cancel_job(job_id: int) -> ApiResponse:
    job_id = Validation.require_id(job_id, "jobs_id")
    data = job_service.cancel(job_id)
    return ApiResponse(data).success()

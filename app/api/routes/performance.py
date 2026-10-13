from fastapi import APIRouter

from app.models.request import PerformanceRequest
from app.models.response import ApiResponse
from app.services.system_service import system_service

router = APIRouter(prefix="/api/performance", tags=["Performance"])


@router.get("")
def get_performance() -> ApiResponse:
    """Performance settings, presets, this computer's hardware and the recommended preset."""
    data = system_service.performance()
    return ApiResponse(data).success()


@router.post("")
def save_performance(body: PerformanceRequest) -> ApiResponse:
    """`preset` fills in every value; any value given replaces the preset's."""
    data = system_service.save_performance(body)
    return ApiResponse(data).success()

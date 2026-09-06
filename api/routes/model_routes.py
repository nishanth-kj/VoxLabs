from fastapi import APIRouter, Depends

from models import APIResponse
from services.model_service import ModelService
from utils.response_handler import ApiResponse
from utils.logger import logger

router = APIRouter(prefix="/api/models", tags=["Models"])


def get_model_service() -> ModelService:
    return ModelService()


@router.get("", response_model=APIResponse)
async def list_models(service: ModelService = Depends(get_model_service)):
    """List every synthesis engine and available voice model."""
    logger.info("GET /api/models - Listing models")
    return ApiResponse(data=await service.list_models()).success()

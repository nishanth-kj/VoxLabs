from fastapi import APIRouter, Depends

from services.system_service import SystemService
from models import APIResponse
from utils.response_handler import ApiResponse
from utils.logger import logger

router = APIRouter(tags=["System"])


def get_system_service() -> SystemService:
    return SystemService()


@router.get("/", response_model=APIResponse)
async def root():
    """API root endpoint"""
    logger.info("GET / - Root endpoint requested")
    data = {
        "name": "VoxLabs API",
        "version": "2.1.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "tts": "/api/tts",
            "voices": "/api/voices"
        }
    }
    return ApiResponse(data=data).success()


@router.get("/api/status", response_model=APIResponse)
async def get_status(service: SystemService = Depends(get_system_service)):
    """Get API status via System Service"""
    logger.info("GET /api/status - Status requested")
    return ApiResponse(data=service.get_status()).success()


@router.get("/api/emotions", response_model=APIResponse)
async def get_emotions(service: SystemService = Depends(get_system_service)):
    """Get available emotions via System Service"""
    logger.info("GET /api/emotions - Emotions requested")
    return ApiResponse(data=service.get_emotions()).success()


@router.get("/api/logs", response_model=APIResponse)
async def get_logs(limit: int = 200, service: SystemService = Depends(get_system_service)):
    """Recent backend logs for the Studio panel. Not written to the request log."""
    return ApiResponse(data=service.get_logs(limit)).success()

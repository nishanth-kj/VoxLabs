from fastapi import APIRouter
from services.system_service import SystemService
from models import EmotionsResponse, StatusResponse
from utils.response_handler import ApiResponse
from utils.logger import logger

class SystemRoutes:
    def __init__(self):
        self.router = APIRouter(tags=["System"])
        self.service = SystemService()
        
        self.router.add_api_route("/", self.root, methods=["GET"])
        self.router.add_api_route("/api/status", self.get_status, methods=["GET"])
        self.router.add_api_route("/api/emotions", self.get_emotions, methods=["GET"])

    async def root(self):
        """API root endpoint"""
        try:
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
        except Exception as e:
            logger.error(f"Error in root endpoint: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

    async def get_status(self):
        """Get API status via System Service"""
        try:
            logger.info("GET /api/status - Status requested")
            status_data = self.service.get_status()
            return ApiResponse(data=status_data).success()
        except Exception as e:
            logger.error(f"Error in get_status endpoint: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

    async def get_emotions(self):
        """Get available emotions via System Service"""
        try:
            logger.info("GET /api/emotions - Emotions requested")
            emotions_data = self.service.get_emotions()
            return ApiResponse(data=emotions_data).success()
        except Exception as e:
            logger.error(f"Error in get_emotions endpoint: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

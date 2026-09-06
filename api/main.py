"""
VoxLabs - FastAPI Backend with Advanced Voice Engine
Professional voice cloning and TTS platform
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sys
import time
import uuid

from routes import get_router
import uvicorn
from utils.logger import logger
from utils.response_handler import ApiResponse
from exceptions import ApiException

try:
    logger.info("Initializing VoxLabs API...")
    # Initialize FastAPI app
    app = FastAPI(
        title="VoxLabs API",
        description="Professional AI Voice Cloning Platform with Advanced Engine",
        version="2.1.0"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and logging middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        quiet = request.url.path == "/api/logs"
        if not quiet:
            logger.info(f"[{request_id}] Start {request.method} {request.url.path}")

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        if not quiet:
            logger.info(f"[{request_id}] Completed {request.method} {request.url.path} in {process_time:.4f}s")
        return response

    # Global error handling - routes/services just raise, this is the only place
    # that turns an exception into a standardized ApiResponse error.
    @app.exception_handler(ApiException)
    async def api_exception_handler(request: Request, exc: ApiException):
        logger.warning(f"{request.method} {request.url.path} - ApiException: {exc.code} {exc.message}")
        return ApiResponse(error=exc).error()

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"{request.method} {request.url.path} - Unhandled error: {exc}", exc_info=True)
        return ApiResponse(error=exc).error()

    # Create directories
    STATIC_DIR = Path("static")
    AUDIO_DIR = STATIC_DIR / "audio"
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Static directories ensured at {STATIC_DIR}")

    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")

    # Include Refactored Routes
    app.include_router(get_router())
    logger.info("Routes and middleware configured successfully.")

except Exception as e:
    logger.error(f"Failed to initialize FastAPI application: {str(e)}", exc_info=True)
    sys.exit(1)

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()

    is_frozen = getattr(sys, "frozen", False)
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8942"))

    try:
        logger.info("Starting VoxLabs API with Advanced Voice Engine...")
        logger.info(f"API: http://127.0.0.1:{API_PORT}")
        if not is_frozen:
            logger.info(f"Docs: http://127.0.0.1:{API_PORT}/docs")

        uvicorn.run(
            app if is_frozen else "main:app",
            host=API_HOST,
            port=API_PORT,
            reload=not is_frozen
        )
    except Exception as e:
        logger.error(f"Runtime error: {str(e)}", exc_info=True)


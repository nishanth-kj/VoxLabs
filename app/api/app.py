"""Optional REST API. Every route calls the same services the desktop UI uses.

Run: uv run uvicorn app.api.app:app            (binds 127.0.0.1 by default)
Set VOXLABS_API_TOKEN (or Settings > API token) to require `Authorization: Bearer <token>`.

Every response is HTTP 200 with the ApiResponse envelope; `status` 1/0 tells
success from failure and `data.type` names the error class.
"""

import hmac
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import audio, clone, health, jobs, models, projects, scripts, tts, users, voices
from app.exceptions import AppError
from app.models.response import ApiResponse
from app.services.system_service import VERSION, system_service
from app.utils.logger import logger

PUBLIC_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}


def _api_token() -> str:
    return os.getenv("VOXLABS_API_TOKEN") or system_service.get_setting("api_token") or ""


def _failure(message: str, error_type: str, field: str | None = None) -> JSONResponse:
    return JSONResponse(status_code=200, content=ApiResponse.failure(message, error_type, field).model_dump())


@asynccontextmanager
async def lifespan(_app: FastAPI):
    system_service.initialize()
    yield


def create_app(initialize: bool = True) -> FastAPI:
    api = FastAPI(
        title="VoxLabs API",
        description="Local REST API for VoxLabs voice cloning, TTS and audio production.",
        version=VERSION,
        lifespan=lifespan if initialize else None,
    )

    @api.middleware("http")
    async def auth_and_log(request: Request, call_next):
        token = _api_token()
        if token and request.url.path not in PUBLIC_PATHS:
            supplied = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
            if not hmac.compare_digest(supplied, token):
                return _failure("Missing or invalid API token", "AuthError")
        started = time.perf_counter()
        response = await call_next(request)
        logger.info(f"API {request.method} {request.url.path} ({(time.perf_counter() - started) * 1000:.0f} ms)")
        return response

    @api.exception_handler(AppError)
    async def app_error(_request: Request, exc: AppError):
        return _failure(exc.message, type(exc).__name__, exc.field)

    @api.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        field = ".".join(str(p) for p in first.get("loc", [])[1:]) or None
        return _failure(f"Invalid request: {first.get('msg', 'validation error')}", "ValidationError", field)

    @api.exception_handler(StarletteHTTPException)
    async def http_error(_request: Request, exc: StarletteHTTPException):
        return _failure(str(exc.detail), "HTTPError")

    @api.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error(f"Unhandled error on {request.method} {request.url.path}", exc_info=exc)
        return _failure("Internal server error", "InternalError")

    # clone before voices so /api/voices/clone isn't matched as /api/voices/{voice_id}
    for module in (health, users, clone, voices, tts, scripts, audio, projects, models, jobs):
        api.include_router(module.router)
    return api


app = create_app()


def run(host: str | None = None, port: int | None = None) -> None:
    """Entry point used by `python -m app.api.app`."""
    import uvicorn

    settings = system_service.get_settings()
    uvicorn.run(app, host=host or settings["api_host"], port=port or int(settings["api_port"]))


if __name__ == "__main__":
    run()

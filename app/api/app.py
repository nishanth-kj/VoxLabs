"""Optional REST API and MCP server. Both call the same services the desktop UI uses.

    uv run python -m app.api.app            REST API + MCP over HTTP (POST /mcp)
    uv run python -m app.api.app --stdio    the same, plus MCP over stdin/stdout for local MCP clients
    uv run uvicorn app.api.app:app          REST API + MCP over HTTP (binds 127.0.0.1 by default)

Set VOXLABS_API_TOKEN (or Settings > API token) to require `Authorization: Bearer <token>`
on every route except health and the docs (this includes /mcp).

Every REST response is HTTP 200 with the ApiResponse envelope; `status` 1/0 tells
success from failure, and failures carry an `error` object (error_code,
error_message, field) built from the predefined ErrorCode / ErrorMessage constants.
"""

import argparse
import hmac
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.mcp import create_mcp_server, http_routes, run_stdio
from app.api.routes import audio, clone, health, jobs, models, projects, scripts, tts, users, voices
from app.exceptions import AppError, AuthError, InternalError, NotFoundError, ValidationError
from app.models.response import ApiResponse
from app.services.system_service import VERSION, system_service
from app.utils.logger import logger

PUBLIC_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}


def _api_token() -> str:
    return os.getenv("VOXLABS_API_TOKEN") or system_service.get_setting("api_token") or ""


def create_app(initialize: bool = True, host: str | None = None) -> FastAPI:
    """The FastAPI app: REST routes under /api and the MCP streamable-HTTP endpoint at /mcp."""
    mcp = create_mcp_server()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        if initialize:
            system_service.initialize()
        async with mcp.session_manager.run():
            yield

    api = FastAPI(
        title="VoxLabs API",
        description="Local REST API and MCP server for VoxLabs voice cloning, TTS and audio production.",
        version=VERSION,
        lifespan=lifespan,
    )

    @api.middleware("http")
    async def auth_and_log(request: Request, call_next):
        token = _api_token()
        if token and request.url.path not in PUBLIC_PATHS:
            supplied = request.headers.get("authorization", "").removeprefix("Bearer ").strip()
            if not hmac.compare_digest(supplied, token):
                logger.warning(f"API {request.method} {request.url.path} rejected: missing or invalid token")
                return ApiResponse(error=AuthError("Missing or invalid API token")).error()
        started = time.perf_counter()
        response = await call_next(request)
        logger.info(f"API {request.method} {request.url.path} ({(time.perf_counter() - started) * 1000:.0f} ms)")
        return response

    @api.exception_handler(AppError)
    async def app_error(_request: Request, exc: AppError):
        return ApiResponse(error=exc).error()

    @api.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        fields = {".".join(str(p) for p in err.get("loc", [])[1:]) or "body": err.get("msg", "Invalid value")
                  for err in exc.errors()}
        logger.warning(f"API {request.method} {request.url.path} invalid request: {', '.join(fields)}")
        return ApiResponse(error=ValidationError("Invalid request", field=fields)).error()

    @api.exception_handler(StarletteHTTPException)
    async def http_error(_request: Request, exc: StarletteHTTPException):
        error = NotFoundError(str(exc.detail)) if exc.status_code == 404 else AppError(str(exc.detail))
        return ApiResponse(error=error).error()

    @api.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error(f"Unhandled error on {request.method} {request.url.path}", exc_info=exc)
        return ApiResponse(error=InternalError()).error()

    # clone before voices so /api/voices/clone isn't matched as /api/voices/{voice_id}
    for module in (health, users, clone, voices, tts, scripts, audio, projects, models, jobs):
        api.include_router(module.router)
    api.router.routes.extend(http_routes(mcp, host or system_service.get_setting("api_host") or "127.0.0.1"))
    return api


app = create_app()


def run(host: str | None = None, port: int | None = None, stdio: bool = False) -> None:
    """Entry point for `python -m app.api.app`.

    With `stdio`, the HTTP server (REST + MCP) runs on a background thread and MCP is
    also served on stdin/stdout; the process ends when the MCP client closes stdin.
    """
    import threading

    import uvicorn

    settings = system_service.get_settings()
    host = host or settings["api_host"] or "127.0.0.1"
    port = port or int(settings["api_port"])
    server = uvicorn.Server(uvicorn.Config(create_app(host=host), host=host, port=port, log_level="warning"))
    logger.info(f"VoxLabs API on http://{host}:{port} (REST /api, MCP /mcp)")
    if not stdio:
        server.run()
        return
    thread = threading.Thread(target=server.run, name="voxlabs-api", daemon=True)
    thread.start()
    try:
        run_stdio()
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser(description="VoxLabs REST API and MCP server")
    parser.add_argument("--host", help="bind address (default: settings api_host, 127.0.0.1)")
    parser.add_argument("--port", type=int, help="port (default: settings api_port, 8942)")
    parser.add_argument("--stdio", action="store_true", help="also serve MCP over stdin/stdout")
    args = parser.parse_args()
    run(args.host, args.port, args.stdio)


if __name__ == "__main__":
    main()

"""The VoxLabs MCP server (Model Context Protocol), over stdio and streamable HTTP.

Every transport serves the same tools (app/api/mcp/tools.py), which call the same services as the REST
API and the desktop UI, and every call is logged in `mcp_calls` (the desktop app's MCP page shows it).

    stdio:      uv run voxlabs-mcp                    (only MCP; no window, no port)
                VoxLabs.exe --mcp                     (the same, from the installed app)
                uv run python -m app.api.app --stdio  (REST + MCP HTTP start too)
    HTTP:       POST http://127.0.0.1:8942/mcp        (mounted by app/api/app.py, wherever the API runs)
                uv run voxlabs-mcp --http             (only MCP, on its own port: 8943)
"""

import argparse
import contextvars
import hmac
import json
import os
import time
from functools import lru_cache
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from starlette.routing import BaseRoute

from app.api.mcp.tools import register_tools
from app.constants.mcp import MCP_HTTP_PORT, MCP_SERVER_NAME
from app.exceptions import AppError
from app.services.mcp_service import mcp_service
from app.services.system_service import VERSION, system_service
from app.utils.logger import log_source, logger

MCP_PATH = "/mcp"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")

INSTRUCTIONS = (
    "VoxLabs is a local voice studio. Use generate_speech for text-to-speech, save_script + generate_script "
    "for lessons and multi-speaker dialogue, process_audio to enhance or edit audio, list_library to see "
    "everything VoxLabs keeps, load_model/get_performance to manage models and speed, and get_job to follow "
    "background work. Every tool returns {status, data, error}; status 1 is success. Voice cloning needs "
    "the speaker's recorded consent and is only available in the desktop app."
)

# Which transport a call came in on, for the call log. The stdio server sets "stdio" before it starts.
TRANSPORT: contextvars.ContextVar[str] = contextvars.ContextVar("mcp_transport", default="http")


class VoxLabsMCP(MCPServer):
    """MCPServer that logs every tool call (arguments, outcome, time) in `mcp_calls`, whatever the transport.

    Recording happens here, at the one place every call passes, so unknown tools and arguments that fail
    validation are logged too. A logging failure never fails the call."""

    async def call_tool(self, name: str, arguments: dict[str, Any], context=None):
        started = time.perf_counter()
        try:
            result = await super().call_tool(name, arguments, context)
        except Exception as exc:
            self._record(name, arguments, started, error=_error_text(exc))
            raise
        self._record(name, arguments, started, result=_result_payload(result))
        return result

    @staticmethod
    def _record(name: str, arguments: dict, started: float, result=None, error: str | None = None) -> None:
        try:
            mcp_service.record(name, arguments, TRANSPORT.get(), (time.perf_counter() - started) * 1000,
                               result=result, error=error)
        except Exception as exc:  # the call itself already succeeded or failed on its own terms
            logger.debug(f"Could not log the MCP call {name}: {exc!r}")


def _result_payload(result) -> Any:
    """Extract structured data or JSON payload from a CallToolResult."""
    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured
    content = getattr(result, "content", None)
    if isinstance(content, (list, tuple)) and content:
        first = content[0]
        text = getattr(first, "text", None)
        if isinstance(text, str):
            try:
                return json.loads(text.split(": ", 1)[-1] if getattr(result, "is_error", False) else text)
            except Exception:
                return text
    return None


def _error_text(exc: BaseException) -> str:
    """The error message of a failed call: the envelope's error_message for VoxLabs errors."""
    text = str(exc) or type(exc).__name__
    if isinstance(exc, ToolError):
        try:
            error = json.loads(text.split(": ", 1)[-1] if not text.startswith("{") else text).get("error") or {}
            return error.get("error_message", text) + (f" ({error['field']})" if error.get("field") else "")
        except (ValueError, AttributeError):
            pass
    return text


def create_mcp_server() -> MCPServer:
    """A new MCP server with every VoxLabs tool registered (one per transport / app instance)."""
    mcp = VoxLabsMCP(MCP_SERVER_NAME, title="VoxLabs", version=VERSION, instructions=INSTRUCTIONS)
    register_tools(mcp)
    return mcp


@lru_cache(maxsize=1)
def tool_catalog() -> tuple[dict, ...]:
    """Every tool an agent can call: name, description and whether it only reads (for the MCP page)."""
    tools = create_mcp_server()._tool_manager.list_tools()
    return tuple({"name": tool.name, "description": tool.description,
                  "read_only": bool(tool.annotations and tool.annotations.read_only_hint),
                  "destructive": bool(tool.annotations and tool.annotations.destructive_hint)}
                 for tool in sorted(tools, key=lambda t: t.name))


def http_routes(mcp: MCPServer, host: str = "127.0.0.1") -> list[BaseRoute]:
    """Streamable-HTTP routes for `MCP_PATH`, to add to the FastAPI app.

    On a loopback host the SDK also rejects foreign Host/Origin headers (DNS rebinding protection).
    The caller must run `mcp.session_manager.run()` in its lifespan.
    """
    app = mcp.streamable_http_app(streamable_http_path=MCP_PATH, host=host if host in LOOPBACK_HOSTS else "0.0.0.0")
    return list(app.routes)


def run_stdio() -> None:
    """Serve MCP on stdin/stdout until the client closes the stream (logs go to stderr)."""
    TRANSPORT.set("stdio")
    logger.info("MCP stdio server started")
    create_mcp_server().run("stdio")
    logger.info("MCP stdio server stopped")


def run_http(host: str, port: int) -> None:
    """Serve only MCP over streamable HTTP. Beyond this computer it needs the API token, like the REST API."""
    import uvicorn

    system_service.check_api_host(host)
    app = create_mcp_server().streamable_http_app(streamable_http_path=MCP_PATH,
                                                  host=host if host in LOOPBACK_HOSTS else "0.0.0.0")
    token = os.getenv("VOXLABS_API_TOKEN") or system_service.get_setting("api_token") or ""

    async def guarded(scope, receive, send):
        if token and scope["type"] == "http":
            supplied = dict(scope["headers"]).get(b"authorization", b"").decode().removeprefix("Bearer ").strip()
            if not hmac.compare_digest(supplied, token):
                await send({"type": "http.response.start", "status": 401,
                            "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": b'{"error": "Missing or invalid API token"}'})
                return
        await app(scope, receive, send)

    logger.info(f"VoxLabs MCP server on http://{host}:{port}{MCP_PATH}")
    uvicorn.run(guarded, host=host, port=port, log_level="warning")


def main(argv: list[str] | None = None) -> int:
    """`voxlabs-mcp`: run only the MCP server (stdio by default, or HTTP on its own port)."""
    parser = argparse.ArgumentParser(prog="voxlabs-mcp", description="VoxLabs MCP server")
    parser.add_argument("--http", action="store_true", help=f"serve streamable HTTP at {MCP_PATH} instead of stdio")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=MCP_HTTP_PORT, help=f"HTTP port (default {MCP_HTTP_PORT})")
    args = parser.parse_args(argv)
    with log_source("mcp"):
        try:
            system_service.initialize()
            run_http(args.host, args.port) if args.http else run_stdio()
        except AppError as exc:
            raise SystemExit(f"VoxLabs MCP: {exc.message}") from exc
        finally:
            from app.services.job_service import job_service
            from app.services.model_service import model_service

            job_service.shutdown(wait=False)
            model_service.unload_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

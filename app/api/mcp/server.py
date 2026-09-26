"""The VoxLabs MCP server (Model Context Protocol), over stdio and streamable HTTP.

Both transports serve the same tools (app/api/mcp/tools.py), which call the
same services as the REST API and the desktop UI.

    stdio: uv run python -m app.api.app --stdio   (REST + MCP HTTP start too)
    HTTP:  POST http://127.0.0.1:8942/mcp         (mounted by app/api/app.py)
"""

from mcp.server.mcpserver import MCPServer
from starlette.routing import BaseRoute

from app.api.mcp.tools import register_tools
from app.services.system_service import VERSION
from app.utils.logger import logger

MCP_PATH = "/mcp"
LOOPBACK_HOSTS = ("127.0.0.1", "localhost", "::1")

INSTRUCTIONS = (
    "VoxLabs is a local voice studio. Use generate_speech for text-to-speech, save_script + generate_script "
    "for lessons and multi-speaker dialogue, process_audio to enhance or edit audio, and get_job to follow "
    "background work. Every tool returns {status, data, error}; status 1 is success. Voice cloning needs "
    "the speaker's recorded consent and is only available in the desktop app."
)


def create_mcp_server() -> MCPServer:
    """A new MCP server with every VoxLabs tool registered (one per transport / app instance)."""
    mcp = MCPServer("voxlabs", title="VoxLabs", version=VERSION, instructions=INSTRUCTIONS)
    register_tools(mcp)
    return mcp


def http_routes(mcp: MCPServer, host: str = "127.0.0.1") -> list[BaseRoute]:
    """Streamable-HTTP routes for `MCP_PATH`, to add to the FastAPI app.

    On a loopback host the SDK also rejects foreign Host/Origin headers (DNS rebinding protection).
    The caller must run `mcp.session_manager.run()` in its lifespan.
    """
    app = mcp.streamable_http_app(streamable_http_path=MCP_PATH, host=host if host in LOOPBACK_HOSTS else "0.0.0.0")
    return list(app.routes)


def run_stdio() -> None:
    """Serve MCP on stdin/stdout until the client closes the stream (logs go to stderr)."""
    logger.info("MCP stdio server started")
    create_mcp_server().run("stdio")
    logger.info("MCP stdio server stopped")

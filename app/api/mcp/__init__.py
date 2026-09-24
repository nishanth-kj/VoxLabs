"""MCP (Model Context Protocol) server: the VoxLabs services as tools for AI agents, over stdio and HTTP."""

from app.api.mcp.server import MCP_PATH, create_mcp_server, http_routes, run_stdio

__all__ = ["MCP_PATH", "create_mcp_server", "http_routes", "run_stdio"]

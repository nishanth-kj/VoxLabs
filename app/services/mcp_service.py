"""McpService: the MCP call log and how an AI app connects to VoxLabs' MCP server.

Every MCP tool call (any transport, any process) is recorded in `mcp_calls`, so the desktop app's MCP
page shows what agents did even when an MCP client runs VoxLabs in its own process over stdio. Long text
is cut, and secret-looking arguments are never stored.
"""

import os
import shlex
import shutil
import subprocess
import sys

from sqlalchemy import delete, func, select

from app.constants.mcp import MCP_HTTP_PORT, MCP_LOG_LIMIT, MCP_LOG_TEXT_CHARS, MCP_SECRET_FIELDS, MCP_SERVER_NAME
from app.constants.status import Status
from app.exceptions import service_error
from app.models import McpCall
from app.services.system_service import system_service
from app.utils.database import read_session, serialize, transaction
from app.utils.files import PROJECT_ROOT

_LOOPBACK = ("127.0.0.1", "localhost", "::1")


def _clean(value, depth: int = 0):
    """A JSON-safe, size-limited copy for the log: long text cut, secrets masked, deep nesting summarized."""
    if isinstance(value, dict):
        if depth > 4:
            return "{…}"
        return {str(key): "***" if any(word in str(key).lower() for word in MCP_SECRET_FIELDS) else _clean(item, depth + 1)
                for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        items = [_clean(item, depth + 1) for item in list(value)[:50]]
        return items + [f"… {len(value) - 50} more"] if len(value) > 50 else items
    if isinstance(value, str):
        return value if len(value) <= MCP_LOG_TEXT_CHARS else value[:MCP_LOG_TEXT_CHARS] + "…"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _clean(str(value), depth)


def _command_line(command: str, args: list[str]) -> str:
    parts = [command, *args]
    return subprocess.list2cmdline(parts) if os.name == "nt" else shlex.join(parts)


class McpService:
    # ------------------------------------------------------------ call log

    def record(self, tool: str, arguments: dict | None, transport: str, duration_ms: float,
               result=None, error: str | None = None) -> None:
        """Log one tool call and keep only the newest MCP_LOG_LIMIT calls."""
        try:
            with transaction() as session:
                session.add(McpCall(
                    tool=tool[:100], transport=transport[:10], arguments=_clean(arguments or {}),
                    result=_clean(result) if result is not None else None,
                    error=error[:1000] if error else None, duration_ms=round(duration_ms),
                    status=Status.FAILED.code if error else Status.COMPLETED.code,
                ))
                session.flush()
                cutoff = session.scalar(select(McpCall.mcp_calls_id).order_by(McpCall.mcp_calls_id.desc())
                                        .offset(MCP_LOG_LIMIT).limit(1))
                if cutoff is not None:
                    session.execute(delete(McpCall).where(McpCall.mcp_calls_id <= cutoff))
        except Exception as exc:
            raise service_error(exc, "mcp_service.record")

    def list_calls(self, limit: int = 200, tool: str | None = None, failed_only: bool = False,
                   after_id: int = 0) -> list[dict]:
        """Logged calls, newest first. `after_id` returns only calls newer than that one (live refresh)."""
        try:
            with read_session() as session:
                query = select(McpCall).where(McpCall.mcp_calls_id > after_id)
                if tool:
                    query = query.where(McpCall.tool == tool)
                if failed_only:
                    query = query.where(McpCall.status == Status.FAILED.code)
                rows = session.scalars(query.order_by(McpCall.mcp_calls_id.desc()).limit(limit))
                return [serialize(row) for row in rows]
        except Exception as exc:
            raise service_error(exc, "mcp_service.list_calls")

    def summary(self) -> dict:
        """Totals for the MCP page: calls, failures and calls per tool."""
        try:
            with read_session() as session:
                per_tool = dict(session.execute(select(McpCall.tool, func.count()).group_by(McpCall.tool)).all())
                failed = session.scalar(select(func.count()).where(McpCall.status == Status.FAILED.code)) or 0
            return {"calls": sum(per_tool.values()), "failed": failed, "per_tool": per_tool}
        except Exception as exc:
            raise service_error(exc, "mcp_service.summary")

    def clear_calls(self) -> int:
        try:
            with transaction() as session:
                removed = session.execute(delete(McpCall)).rowcount or 0
            return removed
        except Exception as exc:
            raise service_error(exc, "mcp_service.clear_calls")

    # ------------------------------------------------------------ connecting an AI app

    def connection(self) -> dict:
        """How MCP clients start or reach this VoxLabs: a stdio command (no window, no port) and the HTTP URL
        of the API's /mcp endpoint, as ready-to-paste config. The API token itself is never included."""
        try:
            settings = system_service.get_settings()
            host = settings["api_host"] or "127.0.0.1"
            url_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
            http_url = f"http://{url_host}:{settings['api_port']}/mcp"
            token_required = bool(os.getenv("VOXLABS_API_TOKEN") or settings["api_token"])
            if getattr(sys, "frozen", False):  # the installed app runs the server itself
                command, args = sys.executable, ["--mcp"]
            else:
                command, args = shutil.which("uv") or "uv", ["run", "--directory", str(PROJECT_ROOT), "voxlabs-mcp"]
            http_entry: dict = {"type": "http", "url": http_url}
            if token_required:
                http_entry["headers"] = {"Authorization": "Bearer <your API token>"}
            header = ' --header "Authorization: Bearer <your API token>"' if token_required else ""
            return {
                "name": MCP_SERVER_NAME,
                "stdio": {"command": command, "args": args},
                "http": {"url": http_url, "running": system_service.api_running(), "token_required": token_required,
                         "local_only": host in _LOOPBACK},
                "standalone_http_port": MCP_HTTP_PORT,
                "claude_desktop": {"mcpServers": {MCP_SERVER_NAME: {"command": command, "args": args}}},
                "claude_code": f"claude mcp add {MCP_SERVER_NAME} -- {_command_line(command, args)}",
                "http_config": {"mcpServers": {MCP_SERVER_NAME: http_entry}},
                "claude_code_http": f"claude mcp add --transport http {MCP_SERVER_NAME} {http_url}{header}",
            }
        except Exception as exc:
            raise service_error(exc, "mcp_service.connection")


mcp_service = McpService()

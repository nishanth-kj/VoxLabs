"""The MCP server: tools answer with the REST envelope, over in-process, HTTP and stdio transports."""

import asyncio
import json
import socket
import sys
import threading
import time
from pathlib import Path

import uvicorn
from mcp import Client, StdioServerParameters

from app.api.app import create_app
from app.api.mcp import create_mcp_server
from app.constants.status import Status

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def payload(result) -> dict:
    """The JSON text of a tool result (success envelope, or the error envelope of a failed call)."""
    return json.loads(result.content[0].text.split(": ", 1)[-1] if result.is_error else result.content[0].text)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_tools_call_services_and_return_the_envelope():
    async def scenario():
        async with Client(create_mcp_server()) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
            assert {"generate_speech", "save_script", "get_job", "process_audio"} <= names
            assert "clone_voice" not in names  # consent must come from the speaker, not an agent

            speech = payload(await client.call_tool("generate_speech", {"body": {"text": "Hello from MCP."}}))
            assert speech["status"] == 1 and speech["data"]["ai_generated"] is True

            missing = await client.call_tool("get_voice", {"voices_id": 999})
            assert missing.is_error
            assert payload(missing) == {"status": 0, "data": None, "error": {
                "error_code": 404, "error_message": "The requested item was not found.",
                "field": {"voices_id": "Voice 999 not found"}}}

            user = payload(await client.call_tool("save_user", {"body": {"name": "Ada"}}))["data"]
            deleted = await client.call_tool("save_user", {"body": {"users_id": user["users_id"],
                                                                    "status": Status.DELETED.code}})
            assert payload(deleted)["data"]["status_label"] == "Deleted"

    asyncio.run(scenario())


def test_http_transport_is_mounted_on_the_api():
    port = free_port()
    server = uvicorn.Server(uvicorn.Config(create_app(initialize=False), host="127.0.0.1", port=port,
                                           log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        deadline = time.time() + 20
        while not server.started and time.time() < deadline:
            time.sleep(0.05)

        async def scenario():
            async with Client(f"http://127.0.0.1:{port}/mcp") as client:
                return payload(await client.call_tool("health", {}))

        assert asyncio.run(scenario())["status"] == 1
    finally:
        server.should_exit = True
        thread.join(timeout=10)


def test_stdio_transport_runs_with_the_http_server(tmp_path):
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.api.app", "--stdio", "--port", str(free_port())],
        env={"VOXLABS_DATA_DIR": str(tmp_path / "stdio-data")},
        cwd=PROJECT_ROOT,
    )

    async def scenario():
        async with Client(params, read_timeout_seconds=60) as client:
            return payload(await client.call_tool("health", {}))

    health = asyncio.run(scenario())
    assert health["status"] == 1 and health["data"]["status"] == "ok"

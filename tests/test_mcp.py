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
from app.api.mcp import create_mcp_server, tool_catalog
from app.constants.status import Status
from app.services import mcp_service as mcp_service_module
from app.services.mcp_service import mcp_service
from app.services.system_service import system_service

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


def test_every_tool_call_is_logged_with_its_outcome():
    async def scenario():
        async with Client(create_mcp_server()) as client:
            await client.call_tool("generate_speech", {"body": {"text": "Logged speech."}})
            await client.call_tool("get_voice", {"voices_id": 999})
            await client.call_tool("no_such_tool", {})

    asyncio.run(scenario())
    failed_unknown, failed_voice, ok = mcp_service.list_calls()
    assert ok["tool"] == "generate_speech" and ok["status"] == Status.COMPLETED.code
    assert ok["arguments"] == {"body": {"text": "Logged speech."}} and ok["duration_ms"] >= 0
    assert ok["result"]["status"] == 1 and ok["result"]["data"]["ai_generated"] is True
    assert failed_voice["status"] == Status.FAILED.code and "Voice 999 not found" in failed_voice["error"]
    assert failed_unknown["tool"] == "no_such_tool" and failed_unknown["status"] == Status.FAILED.code
    summary = mcp_service.summary()
    assert summary == {"calls": 3, "failed": 2, "per_tool": {"generate_speech": 1, "get_voice": 1, "no_such_tool": 1}}
    assert [c["tool"] for c in mcp_service.list_calls(failed_only=True)] == ["no_such_tool", "get_voice"]
    assert mcp_service.list_calls(after_id=ok["mcp_calls_id"])[-1]["tool"] == "get_voice"
    assert mcp_service.clear_calls() == 3 and mcp_service.list_calls() == []


def test_the_log_masks_secrets_cuts_long_text_and_stays_bounded(monkeypatch):
    monkeypatch.setattr(mcp_service_module, "MCP_LOG_LIMIT", 3)
    mcp_service.record("save_user", {"api_token": "s3cret", "body": {"name": "x" * 2000}}, "stdio", 12.4)
    (call,) = mcp_service.list_calls()
    assert call["arguments"]["api_token"] == "***" and len(call["arguments"]["body"]["name"]) == 501
    assert call["transport"] == "stdio" and call["duration_ms"] == 12
    for index in range(5):
        mcp_service.record(f"tool_{index}", {}, "http", 1)
    assert [c["tool"] for c in mcp_service.list_calls()] == ["tool_4", "tool_3", "tool_2"]


def test_tools_for_files_models_and_performance(voice_wav):
    from app.services.audio_service import audio_service

    audio = audio_service.import_file(voice_wav)

    async def scenario():
        async with Client(create_mcp_server()) as client:
            exported = payload(await client.call_tool("save_export", {"body": {"audios_id": audio["audios_id"]}}))
            library = payload(await client.call_tool("list_library", {}))
            loaded = payload(await client.call_tool("load_model", {"model_key": "fake-tts", "background": False}))
            in_memory = payload(await client.call_tool("loaded_models", {}))
            fast = payload(await client.call_tool("save_performance", {"body": {"preset": "low_memory",
                                                                                "batch_size": 2}}))
            current = payload(await client.call_tool("get_performance", {}))
            return exported, library, loaded, in_memory, fast, current

    exported, library, loaded, in_memory, fast, current = asyncio.run(scenario())
    assert exported["data"]["exists"] and {i["kind"] for i in library["data"]} == {"imported", "export"}
    assert loaded["data"]["loaded"] and [m["key"] for m in in_memory["data"]] == ["fake-tts"]
    assert fast["data"]["settings"]["max_loaded_models"] == 1 and fast["data"]["settings"]["batch_size"] == 2
    assert current["data"]["preset"] == "custom" and "recommended_preset" in current["data"]["hardware"]
    names = {tool["name"] for tool in tool_catalog()}
    assert {"list_library", "save_export", "load_model", "loaded_models", "save_performance"} <= names
    assert next(t for t in tool_catalog() if t["name"] == "list_library")["read_only"]


def test_connection_config_for_this_install(monkeypatch):
    system_service.update_settings(api_token="never-shown")
    source = mcp_service.connection()
    assert source["stdio"]["args"][-1] == "voxlabs-mcp" and "--directory" in source["stdio"]["args"]
    assert source["claude_desktop"]["mcpServers"]["voxlabs"] == source["stdio"]
    assert source["claude_code"].startswith("claude mcp add voxlabs -- ")
    assert source["http"]["url"].endswith(":8942/mcp") and source["http"]["token_required"]
    assert "never-shown" not in json.dumps(source)  # the token itself never goes into copied config
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Program Files\VoxLabs\VoxLabs.exe")
    installed = mcp_service.connection()
    assert installed["stdio"] == {"command": r"C:\Program Files\VoxLabs\VoxLabs.exe", "args": ["--mcp"]}


def _stdio_health(tmp_path, args: list[str]) -> dict:
    params = StdioServerParameters(command=sys.executable, args=args, cwd=PROJECT_ROOT,
                                   env={"VOXLABS_DATA_DIR": str(tmp_path / "data")})  # the test's own database

    async def scenario():
        async with Client(params, read_timeout_seconds=60) as client:
            names = {tool.name for tool in (await client.list_tools()).tools}
            assert "list_library" in names
            return payload(await client.call_tool("health", {}))

    return asyncio.run(scenario())


def test_standalone_server_logs_stdio_calls_where_the_desktop_app_sees_them(tmp_path):
    """`voxlabs-mcp` runs only MCP; its calls land in the shared database the MCP page reads."""
    assert _stdio_health(tmp_path, ["-m", "app.api.mcp.server"])["status"] == 1
    (call,) = mcp_service.list_calls()
    assert call["tool"] == "health" and call["transport"] == "stdio" and call["status"] == Status.COMPLETED.code


def test_the_desktop_app_serves_mcp_with_dash_dash_mcp(tmp_path):
    """What the installed app's MCP config runs: `VoxLabs --mcp`, with no window and no port."""
    assert _stdio_health(tmp_path, ["-m", "app.main", "--mcp"])["status"] == 1


def test_performance_routes():
    from fastapi.testclient import TestClient

    client = TestClient(create_app(initialize=False))
    saved = client.post("/api/performance", json={"preset": "quality"}).json()
    assert saved["status"] == 1 and saved["data"]["preset"] == "quality"
    assert saved["data"]["settings"]["precision"] == "full"
    assert client.get("/api/performance").json()["data"]["preset"] == "quality"
    bad = client.post("/api/performance", json={"batch_size": 99}).json()
    assert bad["status"] == 0 and "batch_size" in bad["error"]["field"]

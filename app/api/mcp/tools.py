"""MCP tools. Each tool validates its input, calls the same service the REST route
uses (with the same request class) and returns the same ApiResponse envelope.

Voice cloning is deliberately not exposed: consent must come from the speaker
through the desktop app or the REST form, not from an AI agent.
"""

import json
from collections.abc import Callable
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from app.exceptions import AppError
from app.models.request import (
    AudioExportRequest,
    AudioProcessRequest,
    GenerateScriptRequest,
    ProjectRequest,
    RegenerateRequest,
    ScriptRequest,
    SectionRequest,
    TTSRequest,
    UserRequest,
    VoiceRequest,
)
from app.models.response import ApiResponse
from app.services.audio_service import audio_service
from app.services.job_service import job_service
from app.services.model_service import model_service
from app.services.project_service import project_service
from app.services.script_service import script_service
from app.services.system_service import system_service
from app.services.tts_service import tts_service
from app.services.user_service import user_service
from app.services.voice_service import voice_service
from app.utils.logger import logger
from app.utils.validation import Validation

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False, open_world_hint=False)
SAVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, open_world_hint=False)


def respond(tool: str, call: Callable[[], Any]) -> dict:
    """Run a service call and return the REST envelope; failures become MCP tool errors with the error object."""
    logger.info(f"MCP tool {tool}")
    try:
        return json.loads(bytes(ApiResponse(call()).success().body))
    except AppError as exc:
        raise ToolError(bytes(ApiResponse(error=exc).error().body).decode()) from exc


def register_tools(mcp: MCPServer) -> None:
    # ------------------------------------------------------------ system

    @mcp.tool(description="VoxLabs version, devices, FFmpeg and engine availability.", annotations=READ_ONLY)
    def health() -> dict:
        return respond("health", system_service.health)

    @mcp.tool(description="Emotion, style and enhancement presets accepted by generate_speech and process_audio.",
              annotations=READ_ONLY)
    def presets() -> dict:
        return respond("presets", system_service.presets)

    # ------------------------------------------------------------ users

    @mcp.tool(description="List local users.", annotations=READ_ONLY)
    def list_users() -> dict:
        return respond("list_users", user_service.list_users)

    @mcp.tool(description="Create (no users_id), update (users_id) or delete (users_id + status 8) a user.",
              annotations=SAVE)
    def save_user(body: UserRequest) -> dict:
        return respond("save_user", lambda: user_service.save(body))

    # ------------------------------------------------------------ voices

    @mcp.tool(description="List voices (cloned and preset).", annotations=READ_ONLY)
    def list_voices(include_revoked: bool = False, users_id: int | None = None) -> dict:
        return respond("list_voices", lambda: voice_service.list_voices(
            include_revoked=include_revoked, users_id=Validation.optional_id(users_id, "users_id")))

    @mcp.tool(description="One voice with its samples.", annotations=READ_ONLY)
    def get_voice(voices_id: int) -> dict:
        return respond("get_voice", lambda: voice_service.get(Validation.require_id(voices_id, "voices_id")))

    @mcp.tool(description="Create a preset voice (no voices_id), update (voices_id) or delete (voices_id + status 8). "
                          "Cloned voices need recorded consent and are created in the desktop app.",
              annotations=SAVE)
    def save_voice(body: VoiceRequest) -> dict:
        return respond("save_voice", lambda: voice_service.save(body))

    # ------------------------------------------------------------ speech

    @mcp.tool(description="Generate speech from text. Returns the new audio, or a job with background=true. "
                          "Generated audio is labeled as AI-generated.", annotations=WRITE)
    def generate_speech(body: TTSRequest) -> dict:
        if body.background:
            return respond("generate_speech", lambda: {"job": tts_service.generate_async(body)})
        return respond("generate_speech", lambda: tts_service.generate(body))

    @mcp.tool(description="Generate a new take of an earlier generation (optionally with another seed).",
              annotations=WRITE)
    def regenerate_speech(body: RegenerateRequest) -> dict:
        return respond("regenerate_speech", lambda: tts_service.regenerate(body))

    # ------------------------------------------------------------ audio

    @mcp.tool(description="List audio files in the library (newest first).", annotations=READ_ONLY)
    def list_audio(projects_id: int | None = None, limit: int = 100) -> dict:
        return respond("list_audio", lambda: audio_service.list_audios(
            Validation.optional_id(projects_id, "projects_id"), Validation.limit(limit)))

    @mcp.tool(description="One audio record (path, duration, loudness, AI-generated flag).", annotations=READ_ONLY)
    def get_audio(audios_id: int) -> dict:
        return respond("get_audio", lambda: audio_service.get(Validation.require_id(audios_id, "audios_id")))

    @mcp.tool(description="Enhance audio with steps/preset, or render a non-destructive edit list (ops) "
                          "into a new audio. The source is never changed.", annotations=WRITE)
    def process_audio(body: AudioProcessRequest) -> dict:
        if body.background:
            return respond("process_audio", lambda: {"job": audio_service.process_async(body)})
        return respond("process_audio", lambda: audio_service.process(body))

    @mcp.tool(description="Export audio (wav/flac/ogg/mp3/m4a) into the VoxLabs exports folder; returns the file path.",
              annotations=WRITE)
    def export_audio(body: AudioExportRequest) -> dict:
        return respond("export_audio", lambda: {"path": audio_service.export(body)})

    # ------------------------------------------------------------ scripts

    @mcp.tool(description="List scripts, optionally for one project.", annotations=READ_ONLY)
    def list_scripts(projects_id: int | None = None) -> dict:
        return respond("list_scripts", lambda: script_service.list_scripts(
            Validation.optional_id(projects_id, "projects_id")))

    @mcp.tool(description="One script with its parsed sections, speakers and takes.", annotations=READ_ONLY)
    def get_script(scripts_id: int) -> dict:
        return respond("get_script", lambda: script_service.get(Validation.require_id(scripts_id, "scripts_id")))

    @mcp.tool(description="Create (no scripts_id), update (scripts_id) or delete (scripts_id + status 8) a script. "
                          "'Name: text' lines become speakers; [pause 800ms] adds pauses.", annotations=SAVE)
    def save_script(body: ScriptRequest) -> dict:
        return respond("save_script", lambda: script_service.save(body))

    @mcp.tool(description="Change one script section (voice, speed, pitch, emotion, style, pause, text).",
              annotations=WRITE)
    def update_section(body: SectionRequest) -> dict:
        return respond("update_section", lambda: script_service.update_section(body))

    @mcp.tool(description="Generate every missing section and render the final audio. Runs as a job by default.",
              annotations=WRITE)
    def generate_script(scripts_id: int, body: GenerateScriptRequest | None = None) -> dict:
        scripts_id = Validation.require_id(scripts_id, "scripts_id")
        body = body or GenerateScriptRequest()
        if body.background:
            return respond("generate_script", lambda: {"job": script_service.generate_async(scripts_id, body)})
        return respond("generate_script", lambda: script_service.generate(scripts_id, body))

    # ------------------------------------------------------------ projects

    @mcp.tool(description="List projects.", annotations=READ_ONLY)
    def list_projects(users_id: int | None = None) -> dict:
        return respond("list_projects", lambda: project_service.list_projects(
            users_id=Validation.optional_id(users_id, "users_id")))

    @mcp.tool(description="One project with its scripts, audio and voices.", annotations=READ_ONLY)
    def get_project(projects_id: int) -> dict:
        return respond("get_project", lambda: project_service.open_project(
            Validation.require_id(projects_id, "projects_id")))

    @mcp.tool(description="Create (no projects_id), update (projects_id) or delete (projects_id + status 8) a project.",
              annotations=SAVE)
    def save_project(body: ProjectRequest) -> dict:
        return respond("save_project", lambda: project_service.save(body))

    # ------------------------------------------------------------ models and jobs

    @mcp.tool(description="List TTS/cloning models with install and load state.", annotations=READ_ONLY)
    def list_models(model_type: str | None = None) -> dict:
        return respond("list_models", lambda: model_service.list_models(model_type))

    @mcp.tool(description="List background jobs (newest first).", annotations=READ_ONLY)
    def list_jobs(active: bool = False, limit: int = 50) -> dict:
        return respond("list_jobs", lambda: job_service.list_jobs(active_only=active, limit=Validation.limit(limit)))

    @mcp.tool(description="One background job: status, progress and result.", annotations=READ_ONLY)
    def get_job(jobs_id: int) -> dict:
        return respond("get_job", lambda: job_service.get(Validation.require_id(jobs_id, "jobs_id")))

    @mcp.tool(description="Cancel a queued or running job.", annotations=WRITE)
    def cancel_job(jobs_id: int) -> dict:
        return respond("cancel_job", lambda: job_service.cancel(Validation.require_id(jobs_id, "jobs_id")))

"""API request classes (Pydantic), one class per file. Routes validate input with these."""

from app.models.request.audio_export_request import AudioExportRequest
from app.models.request.audio_process_request import AudioProcessRequest
from app.models.request.generate_script_request import GenerateScriptRequest
from app.models.request.project_request import ProjectRequest
from app.models.request.regenerate_request import RegenerateRequest
from app.models.request.script_request import ScriptRequest
from app.models.request.section_request import SectionRequest
from app.models.request.tts_request import TTSRequest
from app.models.request.user_request import UserRequest
from app.models.request.voice_request import VoiceRequest

__all__ = [
    "AudioExportRequest",
    "AudioProcessRequest",
    "GenerateScriptRequest",
    "ProjectRequest",
    "RegenerateRequest",
    "ScriptRequest",
    "SectionRequest",
    "TTSRequest",
    "UserRequest",
    "VoiceRequest",
]

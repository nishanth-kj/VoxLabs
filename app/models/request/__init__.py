"""API request classes (Pydantic), one class per file. Routes validate input with these and pass them to services."""

from app.models.request.audio_export_request import AudioExportRequest
from app.models.request.audio_import_request import AudioImportRequest
from app.models.request.audio_process_request import AudioProcessRequest
from app.models.request.clone_request import CloneRequest
from app.models.request.dubbing_import_request import DubbingImportRequest
from app.models.request.dubbing_project_request import DubbingProjectRequest
from app.models.request.dubbing_render_request import DubbingRenderRequest
from app.models.request.dubbing_segment_request import DubbingSegmentRequest
from app.models.request.export_request import ExportRequest
from app.models.request.generate_script_request import GenerateScriptRequest
from app.models.request.performance_request import PerformanceRequest
from app.models.request.regenerate_request import RegenerateRequest
from app.models.request.script_request import ScriptRequest
from app.models.request.section_request import SectionRequest
from app.models.request.tts_request import TTSRequest
from app.models.request.user_request import UserRequest
from app.models.request.voice_request import VoiceRequest

__all__ = [
    "AudioExportRequest",
    "AudioImportRequest",
    "AudioProcessRequest",
    "CloneRequest",
    "DubbingImportRequest",
    "DubbingProjectRequest",
    "DubbingRenderRequest",
    "DubbingSegmentRequest",
    "ExportRequest",
    "GenerateScriptRequest",
    "PerformanceRequest",
    "RegenerateRequest",
    "ScriptRequest",
    "SectionRequest",
    "TTSRequest",
    "UserRequest",
    "VoiceRequest",
]

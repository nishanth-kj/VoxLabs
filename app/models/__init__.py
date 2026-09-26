"""SQLAlchemy models. Importing this package registers every table on Base."""

from app.models.audio import Audio
from app.models.job import Job
from app.models.model import Model
from app.models.project import Project
from app.models.script import Script
from app.models.script_section import ScriptSection
from app.models.take import Take
from app.models.user import User
from app.models.voice import Voice
from app.models.voice_consent import VoiceConsent
from app.models.voice_sample import VoiceSample

__all__ = [
    "Audio",
    "Job",
    "Model",
    "Project",
    "Script",
    "ScriptSection",
    "Take",
    "User",
    "Voice",
    "VoiceConsent",
    "VoiceSample",
]

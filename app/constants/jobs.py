"""Job types and which Status codes a job moves through.

Jobs use the shared Status const in their `status` column:
PENDING (queued) → IN_PROGRESS (running) → COMPLETED | FAILED | CANCELLED.
"""

from app.constants.status import Status

JOB_ACTIVE_STATUSES = (Status.PENDING.code, Status.IN_PROGRESS.code)
JOB_FINISHED_STATUSES = (Status.COMPLETED.code, Status.FAILED.code, Status.CANCELLED.code)

JOB_WORKERS = 2


class JobType:
    VOICE_CLONE = "voice_clone"
    TTS = "tts"
    SCRIPT_RENDER = "script_render"
    SECTION_GENERATE = "section_generate"
    AUDIO_PROCESS = "audio_process"
    MODEL_LOAD = "model_load"
    MODEL_INSTALL = "model_install"
    PROJECT_RENDER = "project_render"

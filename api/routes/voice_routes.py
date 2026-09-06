from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
from pathlib import Path
from typing import Optional

from services.voice_service import VoiceEngine, get_voice_engine
from models import APIResponse
from utils.response_handler import ApiResponse
from utils.logger import logger

router = APIRouter(prefix="/api/voices", tags=["Voices"])


@router.get("", response_model=APIResponse)
async def list_voices(
    project_id: Optional[str] = None,
    voice_engine: VoiceEngine = Depends(get_voice_engine),
):
    """List all registered voices"""
    logger.info(f"Listing voices (project_id={project_id})")
    return ApiResponse(data=voice_engine.list_voices(project_id)).success()


@router.post("/register", response_model=APIResponse, status_code=201)
async def register_voice(
    name: str = Form(...),
    consent: bool = Form(...),
    project_id: str = Form("default"),
    audio: UploadFile = File(...),
    voice_engine: VoiceEngine = Depends(get_voice_engine),
):
    """Register a new voice for cloning"""
    suffix = Path(audio.filename or "").suffix
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_path = temp_file.name
        temp_file.write(await audio.read())

    try:
        logger.info(f"Registering voice: {name} (project_id={project_id})")
        voice_id = voice_engine.register_voice(
            audio_path=temp_path,
            voice_name=name,
            consent=consent,
            project_id=project_id,
        )
        return ApiResponse(data={"voice_id": voice_id}, status_code=201).success()
    finally:
        Path(temp_path).unlink(missing_ok=True)


@router.post("/design", response_model=APIResponse, status_code=201)
async def design_voice(
    prompt: str = Form(...),
    project_id: str = Form("default"),
    voice_engine: VoiceEngine = Depends(get_voice_engine),
):
    """Design a new voice from a prompt"""
    logger.info(f"Designing voice with prompt: {prompt} (project_id={project_id})")
    voice_id = voice_engine.design_voice(prompt=prompt, project_id=project_id)
    return ApiResponse(data={"voice_id": voice_id}, status_code=201).success()


@router.get("/{voice_id}", response_model=APIResponse)
async def get_voice(
    voice_id: str,
    voice_engine: VoiceEngine = Depends(get_voice_engine),
):
    """Get voice details"""
    logger.info(f"Fetching voice details: {voice_id}")
    return ApiResponse(data=voice_engine.get_voice_details(voice_id)).success()


@router.get("/{voice_id}/source")
async def get_voice_source(
    voice_id: str,
    voice_engine: VoiceEngine = Depends(get_voice_engine),
):
    """Get raw audio source for a cloned voice"""
    logger.info(f"Fetching voice source for: {voice_id}")
    source_path = voice_engine.get_voice_source_path_or_raise(voice_id)
    return FileResponse(source_path, media_type="audio/wav")


@router.delete("/{voice_id}", response_model=APIResponse)
async def revoke_voice(
    voice_id: str,
    voice_engine: VoiceEngine = Depends(get_voice_engine),
):
    """Revoke/Delete a registered voice"""
    logger.info(f"Revoking voice: {voice_id}")
    return ApiResponse(data=voice_engine.revoke_voice(voice_id)).success()

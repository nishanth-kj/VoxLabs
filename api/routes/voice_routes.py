from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from services.voice_service import get_voice_engine
from pathlib import Path
from typing import Optional
import tempfile
import os
from models import VoiceListResponse, VoiceRegistrationResponse, VoiceIdentityModel
from utils.response_handler import ApiResponse
from utils.logger import logger

class VoiceRoutes:
    def __init__(self):
        self.router = APIRouter(prefix="/api/voices", tags=["Voices"])
        self.voice_engine = get_voice_engine()
        self.audio_dir = Path("static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Register routes
        self.router.add_api_route("", self.list_voices, methods=["GET"])
        self.router.add_api_route("/register", self.register_voice, methods=["POST"])
        self.router.add_api_route("/design", self.design_voice, methods=["POST"])
        self.router.add_api_route("/{voice_id}", self.get_voice, methods=["GET"])
        self.router.add_api_route("/{voice_id}/source", self.get_voice_source, methods=["GET"])
        self.router.add_api_route("/{voice_id}", self.revoke_voice, methods=["DELETE"])

    async def list_voices(self, project_id: Optional[str] = None):
        """List all registered voices"""
        try:
            logger.info(f"Listing voices (project_id={project_id})")
            voices = self.voice_engine.list_voices(project_id)
            return ApiResponse(data={"voices": voices, "count": len(voices)}).success()
        except Exception as e:
            logger.error(f"Error listing voices: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

    async def register_voice(
        self,
        name: str = Form(...),
        consent: bool = Form(...),
        project_id: str = Form("default"),
        audio: UploadFile = File(...)
    ):
        """Register a new voice for cloning"""
        temp_path = None
        try:
            logger.info(f"Registering voice: {name} (project_id={project_id})")
            
            # Save uploaded audio to temporary file
            suffix = Path(audio.filename or "").suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await audio.read()
                tmp.write(content)
                temp_path = tmp.name
            
            logger.debug(f"Temporary audio saved: {temp_path}")
            
            voice_id = self.voice_engine.register_voice(
                audio_path=temp_path,
                voice_name=name,
                consent=consent,
                project_id=project_id
            )
            
            logger.info(f"Voice registered successfully: {voice_id}")
            return ApiResponse(data={"voice_id": voice_id}, status_code=201).success()
        except Exception as e:
            logger.error(f"Error registering voice: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                logger.debug(f"Removed temporary file: {temp_path}")

    async def design_voice(
        self,
        prompt: str = Form(...),
        project_id: str = Form("default")
    ):
        """Design a new voice from a prompt"""
        try:
            logger.info(f"Designing voice with prompt: {prompt} (project_id={project_id})")
            voice_id = self.voice_engine.design_voice(
                prompt=prompt,
                project_id=project_id
            )
            logger.info(f"Voice designed successfully: {voice_id}")
            return ApiResponse(data={"voice_id": voice_id}, status_code=201).success()
        except Exception as e:
            logger.error(f"Error designing voice: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

    async def get_voice(self, voice_id: str):
        """Get voice details"""
        try:
            logger.info(f"Fetching voice details: {voice_id}")
            voice = self.voice_engine.get_voice(voice_id)
            if voice:
                return ApiResponse(data={"voice": voice.to_dict()}).success()
            else:
                logger.warning(f"Voice not found: {voice_id}")
                return ApiResponse(error=f"Voice {voice_id} not found", status_code=404).error()
        except Exception as e:
            logger.error(f"Error fetching voice {voice_id}: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

    async def get_voice_source(self, voice_id: str):
        """Get raw audio source for a cloned voice"""
        try:
            logger.info(f"Fetching voice source for: {voice_id}")
            source_path = self.voice_engine.get_voice_source_path(voice_id)
            if source_path:
                return FileResponse(source_path, media_type="audio/wav")
            else:
                return ApiResponse(error=f"Audio source not found for voice {voice_id}", status_code=404).error()
        except Exception as e:
            logger.error(f"Error fetching voice source: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

    async def revoke_voice(self, voice_id: str):
        """Revoke/Delete a registered voice"""
        try:
            logger.info(f"Revoking voice: {voice_id}")
            self.voice_engine.revoke_voice(voice_id)
            return ApiResponse(data={"message": f"Voice {voice_id} revoked successfully"}).success()
        except Exception as e:
            logger.error(f"Error revoking voice {voice_id}: {str(e)}", exc_info=True)
            return ApiResponse(error=e).error()

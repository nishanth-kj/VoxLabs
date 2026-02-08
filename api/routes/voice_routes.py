from fastapi import APIRouter, UploadFile, File, Form
from services.voice_service import get_voice_engine
from pathlib import Path
from models import VoiceListResponse, VoiceRegistrationResponse, VoiceIdentityModel
from utils.response_handler import ApiResponse

class VoiceRoutes:
    def __init__(self):
        self.router = APIRouter(prefix="/api/voices", tags=["Voices"])
        self.voice_engine = get_voice_engine()
        self.audio_dir = Path("static/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.router.add_api_route("", self.list_voices, methods=["GET"])
        self.router.add_api_route("/register", self.register_voice, methods=["POST"])
        self.router.add_api_route("/{voice_id}", self.get_voice, methods=["GET"])
        self.router.add_api_route("/{voice_id}", self.delete_voice, methods=["DELETE"])

    async def list_voices(self):
        """List all registered voices"""
        try:
            voices = self.voice_engine.list_voices()
            return ApiResponse(data={"voices": voices, "count": len(voices)}).success()
        except Exception as e:
            return ApiResponse(error=e).error()

    async def register_voice(
        self,
        audio_file: UploadFile = File(...),
        voice_name: str = Form(...),
        description: str = Form("")
    ):
        """Register a new voice for cloning"""
        try:
            temp_path = self.audio_dir / f"temp_{audio_file.filename}"
            with open(temp_path, "wb") as f:
                f.write(await audio_file.read())
            
            voice_id = self.voice_engine.register_voice(
                audio_path=str(temp_path),
                name=voice_name,
                description=description,
                consent=True
            )
            
            data = {
                "voice_id": voice_id,
                "name": voice_name,
                "message": f"Voice '{voice_name}' registered successfully"
            }
            return ApiResponse(data=data).success()
        except Exception as e:
            return ApiResponse(error=e).error()

    async def get_voice(self, voice_id: str):
        """Get voice details"""
        try:
            voice = self.voice_engine.get_voice(voice_id)
            if voice:
                return ApiResponse(data={"voice": voice.to_dict()}).success()
            else:
                return ApiResponse(error=f"Voice {voice_id} not found").error(status_code=404)
        except Exception as e:
            return ApiResponse(error=e).error()

    async def delete_voice(self, voice_id: str):
        """Delete a registered voice"""
        try:
            self.voice_engine.revoke_voice(voice_id)
            return ApiResponse(data={"message": f"Voice {voice_id} deleted successfully"}).success()
        except Exception as e:
            return ApiResponse(error=e).error()

from pydantic import BaseModel


class VoiceRegistrationResponse(BaseModel):
    """Successful registration response"""
    voice_id: str
    name: str
    message: str

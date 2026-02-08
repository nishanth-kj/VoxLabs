from fastapi import APIRouter
from .system_routes import SystemRoutes
from .voice_routes import VoiceRoutes
from .tts_routes import TTSRoutes

def get_router() -> APIRouter:
    main_router = APIRouter()
    
    # Initialize classes
    system = SystemRoutes()
    voices = VoiceRoutes()
    tts = TTSRoutes()
    
    # Include their routers
    main_router.include_router(system.router)
    main_router.include_router(voices.router)
    main_router.include_router(tts.router)
    
    return main_router

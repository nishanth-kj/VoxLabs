from fastapi import APIRouter
from .system_routes import router as system_router
from .voice_routes import router as voice_router
from .tts_routes import router as tts_router
from .model_routes import router as model_router

def get_router() -> APIRouter:
    main_router = APIRouter()

    main_router.include_router(system_router)
    main_router.include_router(voice_router)
    main_router.include_router(tts_router)
    main_router.include_router(model_router)

    return main_router

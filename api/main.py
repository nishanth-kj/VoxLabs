"""
VoxLabs - FastAPI Backend with Advanced Voice Engine
Professional voice cloning and TTS platform
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import sys

# Add api directory to path
sys.path.insert(0, str(Path(__file__).parent))

from engine import get_voice_engine
from typing import Optional, Any
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="VoxLabs API",
    description="Professional AI Voice Cloning Platform with Advanced Engine",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
STATIC_DIR = Path("static")
AUDIO_DIR = STATIC_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize voice engine
voice_engine = get_voice_engine()

from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standardized API Response"""
    status: int  # 0 or 1
    data: Optional[T] = None
    error: Optional[str] = None

def api_response(data: Any = None, error: Optional[str] = None) -> APIResponse:
    """Helper to create APIResponse"""
    return APIResponse(
        status=1 if error is None else 0,
        data=data,
        error=error
    )

@app.get("/")
async def root():
    """API root endpoint"""
    return api_response(data={
        "name": "VoxLabs API",
        "version": "2.0.0",
        "status": "running",
        "engine": "advanced",
        "endpoints": {
            "docs": "/docs",
            "tts": "/api/tts",
            "voices": "/api/voices",
            "register": "/api/voices/register",
            "emotions": "/api/emotions"
        }
    })


@app.get("/api/status")
async def get_status():
    """Get API status"""
    return api_response(data={
        "status": "healthy",
        "voice_engine": "advanced",
        "registered_voices": len(voice_engine.list_voices()),
        "engines": ["emotional", "clone", "basic"]
    })


@app.get("/api/emotions")
async def get_emotions():
    """Get available emotions"""
    try:
        from engine.emotional_tts import EmotionalTTSEngine
        engine = EmotionalTTSEngine()
        return api_response(data={
            "emotions": engine.get_emotions(),
            "count": len(engine.get_emotions())
        })
    except Exception as e:
        return api_response(error=str(e))


@app.post("/api/tts")
async def text_to_speech(
    text: str = Form(...),
    engine: str = Form("emotional"),
    voice_id: Optional[str] = Form(None),
    language: str = Form("en"),
    emotion: str = Form("neutral"),
    speed: float = Form(1.0),
    pitch: float = Form(1.0),
    energy: float = Form(1.0)
):
    """
    Generate speech from text using advanced engine
    """
    try:
        # Synthesize using advanced engine
        audio_data = voice_engine.synthesize(
            text=text,
            engine=engine,
            voice_id=voice_id,
            language=language,
            emotion=emotion,
            speed=speed,
            pitch=pitch,
            energy=energy
        )
        
        # Save to file
        filename = f"tts_{hash(text)}_{emotion}.mp3"
        filepath = AUDIO_DIR / filename
        with open(filepath, "wb") as f:
            f.write(audio_data)
        
        return api_response(data={
            "audio_url": f"/static/audio/{filename}",
            "engine": engine,
            "emotion": emotion if engine == "emotional" else None,
            "message": "Speech generated successfully"
        })
    
    except Exception as e:
        return api_response(error=str(e))


@app.get("/api/voices")
async def list_voices():
    """List all registered voices"""
    try:
        voices = voice_engine.list_voices()
        return api_response(data={
            "voices": voices,
            "count": len(voices)
        })
    except Exception as e:
        return api_response(error=str(e))


@app.post("/api/voices/register")
async def register_voice(
    audio_file: UploadFile = File(...),
    voice_name: str = Form(...),
    description: str = Form("")
):
    """
    Register a new voice for cloning
    """
    try:
        # Save uploaded file temporarily
        temp_path = AUDIO_DIR / f"temp_{audio_file.filename}"
        with open(temp_path, "wb") as f:
            f.write(await audio_file.read())
        
        # Register voice
        voice_id = voice_engine.register_voice(
            audio_path=str(temp_path),
            name=voice_name,
            description=description
        )
        
        return api_response(data={
            "voice_id": voice_id,
            "name": voice_name,
            "message": f"Voice '{voice_name}' registered successfully"
        })
    
    except Exception as e:
        return api_response(error=str(e))


@app.delete("/api/voices/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a registered voice"""
    try:
        voice_engine.delete_voice(voice_id)
        return api_response(data={
            "message": f"Voice {voice_id} deleted successfully"
        })
    except Exception as e:
        return api_response(error=str(e))


@app.get("/api/voices/{voice_id}")
async def get_voice(voice_id: str):
    """Get voice details"""
    try:
        voice = voice_engine.get_voice(voice_id)
        if voice:
            return api_response(data={
                "voice": voice
            })
        else:
            return api_response(error="Voice not found")
    except Exception as e:
        return api_response(error=str(e))


if __name__ == "__main__":
    print("🎙️ Starting VoxLabs API with Advanced Voice Engine...")
    print("📍 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("🎭 Emotions: 8 available")
    print("🎤 Voice Cloning: Enabled")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

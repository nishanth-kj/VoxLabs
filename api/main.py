"""
VoxLabs - FastAPI Backend with Advanced Voice Engine
Professional voice cloning and TTS platform
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from routes import get_router
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="VoxLabs API",
    description="Professional AI Voice Cloning Platform with Advanced Engine",
    version="2.1.0"
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

# Include Refactored Routes
app.include_router(get_router())

if __name__ == "__main__":
    print("🎙️ Starting VoxLabs API with Advanced Voice Engine...")
    print("📍 API: http://localhost:8000")
    print("📚 Docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

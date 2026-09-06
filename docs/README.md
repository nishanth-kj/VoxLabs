# VoxLabs

**VoxLabs** is a professional AI-powered Voice Cloning and Text-to-Speech (TTS) platform. It allows users to generate lifelike speech with granular emotional control and clone voices from short audio samples.

## Key Features

- **Advanced Emotional TTS**: Generate speech with specific emotions (Happy, Sad, Angry, etc.) and fine-tune Speed, Pitch, and Energy.
- **Voice Cloning**: Clone any voice using just a 30-second audio sample.
- **Landing site**: A Next.js download page (`site/`) that points visitors to the desktop app.
- **Desktop Application**: The product UI — a Tauri desktop app (`desktop/`) wrapping a Next.js/TypeScript frontend.
- **Robust API**: FastAPI backend with standardized JSON responses.

## Documentation Index

- [**Backend Documentation**](./backend.md): Audio Engine architecture and DSP details.
- [**API Documentation**](./api.md): Detailed API endpoint reference.
- [**Frontend Documentation**](./frontend.md): Landing page architecture and download CTAs.
- [**Setup & Deployment**](./setup.md): Installation guides for Local Development and Docker.

## Technology Stack

- **Backend**: Python 3.12+, FastAPI, Librosa, SoundFile, Uvicorn.
- **Frontend**: TypeScript, Next.js 16, React, Tailwind CSS, Shadcn UI, Framer Motion / GSAP.
- **Desktop**: Tauri (Rust) + Next.js 16 / TypeScript, statically exported.
- **Containerization**: Docker & Docker Compose.

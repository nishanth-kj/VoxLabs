# VoxLabs

**VoxLabs** is a professional AI-powered Voice Cloning and Text-to-Speech (TTS) platform. It allows users to generate lifelike speech with granular emotional control and clone voices from short audio samples.

## Key Features

- **Advanced Emotional TTS**: Generate speech with specific emotions (Happy, Sad, Angry, etc.) and fine-tune Speed, Pitch, and Energy.
- **Voice Cloning**: Clone any voice using just a 30-second audio sample.
- **Modern Studio UI**: A sleek, dark-mode web interface built with Next.js and Tailwind CSS.
- **Desktop Application**: Bundled as a native app using Tauri.
- **Robust API**: FastAPI backend with standardized JSON responses.

## Documentation Index

- [**Backend Documentation**](./backend.md): Audio Engine architecture and DSP details.
- [**API Documentation**](./api.md): Detailed API endpoint reference.
- [**Frontend Documentation**](./frontend.md): Web Studio architecture, State management, and UI components.
- [**Setup & Deployment**](./setup.md): Installation guides for Local Development and Docker.

## Technology Stack

- **Backend**: Python 3.12+, FastAPI, Librosa, SoundFile, Uvicorn.
- **Frontend**: TypeScript, Next.js 16, React, Tailwind CSS, Shadcn UI, Framer Motion / GSAP.
- **Desktop**: Tauri (Rust).
- **Containerization**: Docker & Docker Compose.

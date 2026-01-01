# Setup & Deployment Guide

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 18 or higher
- **FFmpeg**: Required for audio processing (must be in system PATH).

## Quick Start (Docker)

The easiest way to run VoxLabs is using Docker Compose.

1.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```
2.  **Access**:
    - Web Studio: `http://localhost:3000`
    - API Docs: `http://localhost:8000/docs`

## Local Development

If you prefer to run services manually:

### 1. Backend (API)

```bash
cd api
# Install dependencies (using uv or pip)
uv sync  # or pip install -r requirements.txt

# Run Server
uv run uvicorn main:app --reload --port 8000
```

### 2. Frontend (Web)

```bash
cd web
# Install dependencies
npm install

# Run Development Server
npm run dev
```

Visit `http://localhost:3000` to start using the Studio.

## Troubleshooting

- **FFmpeg Error**: If you see errors about "ffmpeg not found", ensure it is installed and added to your system environment variables.
- **API Connection**: Ensure the backend is running on `localhost:8000`. The frontend expects this default URL.

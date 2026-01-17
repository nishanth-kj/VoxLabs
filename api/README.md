# VoxLabs Backend

Python/FastAPI backend for voice cloning and TTS.

## Quick Start

### Using uv (Recommended)

First, install [uv](https://github.com/astral-sh/uv):

```bash
# On Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then run the API:

```bash
uv run python main.py
```

## API Endpoints

- `GET /` - API root
- `POST /api/tts` - Text-to-speech
- `GET /api/voices` - List voices
- `POST /api/voices/register` - Register voice
- `DELETE /api/voices/{id}` - Revoke voice

## Requirements

- Python 3.12+
- `uv` package manager

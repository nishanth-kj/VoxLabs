# VoxLabs Backend

Python/FastAPI backend for voice cloning and TTS.

## Quick Start

```bash
python main.py
```

## API Endpoints

- `GET /` - API root
- `POST /api/tts` - Text-to-speech
- `GET /api/voices` - List voices
- `POST /api/voices/register` - Register voice
- `DELETE /api/voices/{id}` - Revoke voice

## Requirements

- Python 3.12+
- See `requirements.txt`

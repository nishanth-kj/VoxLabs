# Backend Documentation

The backend is built with FastAPI and follows a strict **Routes-Services** class-based architecture.

## Architecture
- **Routes** (`api/routes`): Class-based handlers (`SystemRoutes`, `VoiceRoutes`, `TTSRoutes`) using `APIRouter`.
- **Services** (`api/services`): Dedicated services (`SystemService`, `VoiceService`, `TTSService`, `EdgeTTSService`) containing business logic.

## Setup
```bash
# Git-based setup
git clone ...
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install edge-tts
```

## Endpoints
### Edge TTS
- `GET /api/tts/edge/voices`: List Microsoft AI voices.
- `POST /api/tts/edge/generate`: Generate high-quality voice.

## Audio Engine (DSP)

The `EmotionalTTSEngine` uses `librosa` to apply effects post-synthesis (or during processing):

- **Time Stretching**: `librosa.effects.time_stretch` controls speaking rate.
- **Pitch Shifting**: `librosa.effects.pitch_shift` modifies the tone of the voice.
- **Energy Control**: Volume gain adjustment.

### Emotion Presets

Emotions are defined with default parameters to ensure consistent character representation:

| Emotion | Speed | Pitch | Energy |
| :--- | :--- | :--- | :--- |
| **Neutral** | 1.0 | 1.0 | 1.0 |
| **Happy** | 1.2 | 1.1 | 1.2 |
| **Sad** | 0.8 | 0.9 | 0.8 |
| **Angry** | 1.3 | 0.8 | 1.5 |

*Note: These defaults are exposed via the `/api/emotions` endpoint.*

## API Reference

All API endpoints follow a standardized response format:

```json
{
  "status": 1,      // 1 = Success, 0 = Error
  "data": { ... },  // Payload
  "error": null     // Error message if status is 0
}
```

**For a complete list of endpoints and request/response examples, please refer to the [API Documentation](./api.md).**

# Backend Documentation

The VoxLabs backend is built with **FastAPI** and provides a robust engine for speech synthesis and voice management.

## Architecture

The backend is structured as follows:

- **`main.py`**: The entry point. Initializes the FastAPI app, mounts static files, and defines API endpoints.
- **`engine/`**: Contains the core logic for audio processing.
    - **`emotional_tts.py`**: Implements the `EmotionalTTSEngine`. Uses `librosa` for Digital Signal Processing (DSP) to modify pitch, speed, and energy.
    - **`voice_engine.py`**: Manages voice cloning and synthesis coordination.
- **`static/audio/`**: Stores generated TTS audio files and temporary uploads.

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

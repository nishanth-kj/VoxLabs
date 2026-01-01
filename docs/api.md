# API Documentation

The VoxLabs API is a RESTful service built with FastAPI. It uses a standardized JSON response format for all endpoints.

## Base URL
`http://localhost:8000`

## Response Format
All responses (success or error) share a common structure:

```json
{
  "status": 1,       // 1 for Success, 0 for Error
  "data": { ... },   // The actual payload (null on error)
  "error": null      // Error message string (null on success)
}
```

---

## Endpoints

### 1. General Status
**GET** `/api/status`

Check the health and capabilities of the API.

**Response:**
```json
{
  "status": 1,
  "data": {
    "status": "healthy",
    "voice_engine": "advanced",
    "registered_voices": 5,
    "engines": ["emotional", "clone", "basic"]
  },
  "error": null
}
```

### 2. Emotions
**GET** `/api/emotions`

Retrieve available emotions and their default parameter presets.

**Response:**
```json
{
  "status": 1,
  "data": {
    "emotions": {
      "neutral": { "speed": 1.0, "pitch": 1.0, "energy": 1.0 },
      "happy": { "speed": 1.2, "pitch": 1.1, "energy": 1.2 },
      "sad": { "speed": 0.8, "pitch": 0.9, "energy": 0.8 }
      // ... others
    },
    "count": 8
  },
  "error": null
}
```

### 3. Text to Speech
**POST** `/api/tts`

Generate speech from text.

**Request Body (FormData):**
- `text` (str): The text to synthesize.
- `engine` (str, optional): `emotional` (default) or `clone`.
- `emotion` (str, optional): E.g., `happy`, `sad`. (Used if engine is `emotional`).
- `voice_id` (str, optional): Target voice ID (Used if engine is `clone`).
- `speed` (float, optional): 0.5 - 2.0.
- `pitch` (float, optional): 0.5 - 1.5.
- `energy` (float, optional): 0.5 - 2.0.

**Response:**
```json
{
  "status": 1,
  "data": {
    "audio_url": "/static/audio/tts_384729_happy.mp3",
    "engine": "emotional",
    "emotion": "happy",
    "message": "Speech generated successfully"
  },
  "error": null
}
```

### 4. Voice Management

#### List Voices
**GET** `/api/voices`

**Response:**
```json
{
  "status": 1,
  "data": {
    "voices": [
      { "id": "voice_123", "name": "Narrator", "description": "Cloned from sample" }
    ],
    "count": 1
  },
  "error": null
}
```

#### Register Voice (Clone)
**POST** `/api/voices/register`

Register a new voice model from an audio sample.

**Request Body (Multipart):**
- `audio_file` (File): WAV/MP3 file (~30s recommended).
- `voice_name` (str): Name for the voice.
- `description` (str, optional).

**Response:**
```json
{
  "status": 1,
  "data": {
    "voice_id": "voice_999",
    "name": "My Clone",
    "message": "Voice 'My Clone' registered successfully"
  },
  "error": null
}
```

#### Get Voice Details
**GET** `/api/voices/{voice_id}`

**Response:**
```json
{
  "status": 1,
  "data": {
    "voice": { "id": "voice_999", "name": "My Clone", ... }
  },
  "error": null
}
```

#### Delete Voice
**DELETE** `/api/voices/{voice_id}`

**Response:**
```json
{
  "status": 1,
  "data": {
    "message": "Voice voice_999 deleted successfully"
  },
  "error": null
}
```

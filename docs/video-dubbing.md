# Video Dubbing Studio

Synchronized video dubbing with timestamped subtitle alignment, multi-speaker voice mapping, duration conflict detection, and lossless video remuxing.

```text
Media / Video Ingestion (FFmpeg probe & audio extraction)
       │
Subtitle Parsing / Alignment (SRT / WebVTT with millisecond precision)
       │
Multi-Speaker Auto Mapping (detect unique speakers → assign library voices)
       │
Line-by-Line Synthesis (TTS with exact duration measurement)
       │
Timing Conflict Detection (delta = audio_duration - slot_duration)
  [OK: ±100ms | Overflow: >100ms | Underflow: <-300ms]
       │
Timeline Composition & Background Ducking (-12 dB smooth envelope)
       │
Lossless Video Remuxing (-c:v copy -c:a aac -shortest)
```

## Features

- **Media Ingestion**: Imports MP4, MKV, MOV, WebM, AVI, WAV, or MP3. FFmpeg safely probes video resolution, frame rate, audio sample rate, channels, and extracts the background audio.
- **Subtitle Alignment**: Full SRT and WebVTT support with millisecond precision (`HH:MM:SS,mmm` and `HH:MM:SS.mmm`). Recognizes speaker tags such as `<v Speaker>` and `[Speaker]:`.
- **Speaker Assignment**: Automatically identifies unique speakers across the timeline and pairs each speaker with available voices.
- **Timing Conflict Detection**: Dialogue is never silently stretched, warped, or truncated. Every line measures `generated_duration_ms` against `slot_duration_ms` (`end_ms - start_ms`) and displays exact millisecond deltas in the timeline.
- **Non-Destructive Revision**: Regenerate, adjust speed, pitch, or dialogue text for an individual line without touching approved or locked lines.
- **Audio Ducking**: Automatically attenuates background audio during spoken lines (by default -12 dB / 0.25x volume) with a 40–80 ms smooth attack/release envelope to eliminate clicks.
- **Video Remuxing**: Muxes the synthesized audio track into the original video container using FFmpeg's stream copy (`-c:v copy`), preserving the original video quality with zero generational loss.

## REST API Endpoints

- `GET /api/dubbing`: List all dubbing projects.
- `GET /api/dubbing/{id}`: Retrieve a dubbing project with its timeline segments, speaker assignments, and conflict status.
- `POST /api/dubbing`: Create, update, or delete a dubbing project.
- `POST /api/dubbing/import-subtitles`: Import SRT or WebVTT subtitles into a project.
- `GET /api/dubbing/{id}/subtitles`: Export synchronized subtitles (SRT or WebVTT).
- `POST /api/dubbing/segments`: Update or create an individual timeline segment.
- `POST /api/dubbing/segments/{id}/generate`: Synthesize TTS for a single segment and compute conflict metrics.
- `POST /api/dubbing/{id}/auto-map`: Auto-map unique speakers to library voices.
- `POST /api/dubbing/{id}/generate-all`: Synthesize all pending segments in batch.
- `POST /api/dubbing/render`: Mix audio tracks with ducking and remux the synchronized output video.

## MCP Tools

- `list_dubbing_projects`: List dubbing projects.
- `get_dubbing_project`: Fetch project details, timeline segments, and conflict metrics.
- `save_dubbing_project`: Create, update, or delete a dubbing project.
- `import_dubbing_subtitles`: Import SRT or WebVTT subtitles.
- `render_dubbed_video`: Render synchronized audio and remux the video.


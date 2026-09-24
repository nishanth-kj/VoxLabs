# VoxLabs

**A local-first desktop studio for voice cloning, text-to-speech, narrated lessons and audio editing.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)

VoxLabs is a native Python desktop application (PySide6). An optional REST API exposes the same features to other programs. There is no web app.

## Features

- **Voice cloning with consent.** Import or record samples, get a quality report, record who consented, then clone. Voices can be revoked, which deletes their data, or deleted completely.
- **Text to speech.** Voice, model, speed, pitch, energy, emotion, style, pauses, pronunciations, temperature and seed. You can regenerate a single sentence.
- **Script and lesson to audio.** Chapters, sections and speakers (`Teacher: …`) mapped to voices, with per-section settings, multiple takes, intro/outro, and a final render with a clean-up preset.
- **Audio editor.** Non-destructive waveform editing: select, cut, copy, paste, delete, split, trim, move, duplicate, join, fade, volume, normalize, undo/redo and loop playback.
- **Enhancement.** Denoise, EQ, compression, de-esser, limiter and loudness, with the presets Voice Clean, Podcast, Narration, Lesson, Studio and Raw. Originals are always kept.
- **Projects.** Group scripts, takes and audio. Duplicate projects or export them to a zip. Editor state is autosaved.
- **Local models.** Piper, XTTS v2, F5-TTS and Chatterbox run on this machine (CPU or CUDA). Online engines (Google, Microsoft Edge) are opt-in.
- **Background jobs.** Long work never freezes the UI. You can see progress and cancel jobs.

All generated audio is flagged as AI-generated in the library and tagged in the file metadata.

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/). FFmpeg is optional: WAV, FLAC, OGG and MP3 work without it, and it adds M4A/AAC.

```bash
uv sync                          # base install
uv sync --extra piper            # + Piper, a fast offline TTS engine (recommended)
uv run python -m app.main        # start the desktop app
```

On first launch, open **Models** and install *Piper · en_US Lessac*, a 63 MB download. For real zero-shot cloning, install one of the heavier engines:

```bash
uv sync --extra xtts             # Coqui XTTS v2 (non-commercial CPML license)
uv sync --extra f5               # F5-TTS
uv sync --extra chatterbox       # Chatterbox
```

These pull in PyTorch. A CUDA GPU is strongly recommended.

## Optional REST API

```bash
uv run uvicorn app.api.app:app            # http://127.0.0.1:8000/docs
```

The API can also be started from **Settings → REST API** inside the desktop app. It binds to `127.0.0.1` by default. Set `VOXLABS_API_TOKEN` (or the token in Settings) before exposing it anywhere else. See [docs/rest-api.md](./docs/rest-api.md).

## Data

Everything lives in `data/`: the SQLite database, voices, audio, models, cache and exports. Set `VOXLABS_DATA_DIR` to put it somewhere else. Nothing is uploaded unless you enable an online engine.

## Documentation

- [Architecture](./docs/architecture.md)
- [Database](./docs/database.md)
- [Audio engine](./docs/audio-engine.md)
- [Voice cloning](./docs/voice-cloning.md)
- [TTS](./docs/tts.md)
- [Script to audio](./docs/script-to-audio.md)
- [REST API](./docs/rest-api.md)
- [Development](./docs/development.md)

## Responsible use

Only clone a voice with the speaker's explicit permission. VoxLabs records who granted consent and when. Revoking a voice deletes its samples and profile immediately. Do not use generated audio to deceive or impersonate anyone.

## License

MIT. See [LICENSE](./LICENSE). Model weights have their own licenses (for example, XTTS v2 is non-commercial).

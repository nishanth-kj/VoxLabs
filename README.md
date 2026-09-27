# VoxLabs

**A local desktop studio for voice cloning, text-to-speech, narrated lessons and audio editing.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](./LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)

VoxLabs is a native Python desktop application (PySide6). An optional REST API exposes the same features to other programs. There is no web app. [`site/`](./site) is only the landing page, which points visitors to the desktop download.

## Features

- **Voice cloning with consent.** Import or record samples, get a quality report, record who consented, then clone. Voices can be revoked, which deletes their data, or deleted completely.
- **Text to speech.** Voice, model, speed, pitch, energy, emotion, style, pauses, pronunciations, temperature and seed. You can regenerate a single sentence.
- **Script and lesson to audio.** Chapters, sections and speakers (`Teacher: …`) mapped to voices, with per-section settings, multiple takes, intro/outro, and a final render with a clean-up preset.
- **Audio editor.** Non-destructive waveform editing: select, cut, copy, paste, delete, split, trim, move, duplicate, join, fade, volume, normalize, undo/redo and loop playback.
- **Enhancement.** Denoise, EQ, compression, de-esser, limiter and loudness, with the presets Voice Clean, Podcast, Narration, Lesson, Studio and Raw. Originals are always kept.
- **Takes and autosave.** Every script section keeps its takes, and the audio editor autosaves its edit list on each audio.
- **Local models.** Piper, Kokoro, Chatterbox, Chatterbox Turbo and Qwen3-TTS run on this machine (CPU or CUDA, falling back to the CPU when the GPU is full). Online engines (Google, Microsoft Edge) are opt-in.
- **Background jobs.** Long work never freezes the UI. You can see progress and cancel jobs.

All generated audio is flagged as AI-generated in the library and tagged in the file metadata.

## Quick start

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/). FFmpeg is optional: WAV, FLAC, OGG and MP3 work without it, and it adds M4A/AAC.

```bash
uv sync                          # base install
uv sync --extra piper            # + Piper, a fast offline TTS engine (recommended)
uv run python -m app.main        # start the desktop app
```

On first launch, open **Models** and install *Piper · en_US Lessac*, a 63 MB download. For more natural narration that still runs well on a CPU, add Kokoro (82M parameters, about 330 MB, built-in voices such as `af_heart` and `af_bella`):

```bash
uv sync --extra piper --extra kokoro
```

For real zero-shot cloning, install Chatterbox (it includes Chatterbox Turbo):

```bash
uv sync --extra chatterbox       # Chatterbox (also speaks without a cloned voice, in its built-in voice)
```

These pull in PyTorch. A CUDA GPU is strongly recommended.

Qwen3-TTS needs other library versions than Chatterbox, so it gets its own environment: install it on the Models page and VoxLabs sets up `data/engines/qwen3-tts` with uv (from a source checkout; built apps cannot).

On a slow connection, large wheels (onnxruntime, PyTorch) can hit uv's download timeout. Raise it and retry, e.g. in PowerShell: `$env:UV_HTTP_TIMEOUT = "900"; uv sync --extra piper`.

The window has an Electron-style layout: every command sits in the top menu (File, Edit, View, Voice, Audio, Script, Tools, Help), **Ctrl+Shift+P** searches all of them, **Ctrl+B** collapses the sidebar, and **View → Theme** switches between dark, light and your system theme.

## Optional REST API and MCP server

```bash
uv run python -m app.api.app              # REST API + MCP over HTTP: http://127.0.0.1:8942/docs, /mcp
uv run python -m app.api.app --stdio      # the same, plus MCP over stdin/stdout for local MCP clients
```

The API can also be started from **Settings → REST API** inside the desktop app. It binds to `127.0.0.1` by default. Set `VOXLABS_API_TOKEN` (or the token in Settings) before exposing it anywhere else. AI agents get the same services as MCP tools (voice cloning is left out, because consent must come from the speaker). See [docs/rest-api.md](./docs/rest-api.md).

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

MIT. See [LICENSE](./LICENSE). Model weights have their own licenses; check a model's license before commercial use.

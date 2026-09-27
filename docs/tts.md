# Text to speech

`TTSService` (`app/services/tts_service.py`).

## Pipeline

```text
text → validate → pronunciations → resolve voice → resolve model → load backend
     → chunk (sentence-aligned, [pause] tags; ≤ 400 chars, or the engine's own limit)
     → synthesize each chunk (one generation at a time per engine)
     → join with pauses → pitch-match (profile voices) → prosody DSP
     → save original WAV → clean-up steps → processed WAV → audios row (ai_generated)
```

- `synthesize(...)` returns `(audio, sample_rate, info)` in memory.
- `generate(...)` does the full pipeline and returns the `audios` dict plus `cached`. The raw output is kept as `original_path`.
- `generate_async(...)` does the same in a background job.

### Cache

With `cache: true`, `generate` first hashes everything that changes the sound (text, every speech setting, the resolved model and the voice's last update) and returns the newest generated audio with the same hash whose file still exists, with `cached: true`. Nothing is generated or saved. This is meant for pipelines that regenerate the same lines repeatedly, such as video narration. Leave it off (the default) to get a new take every time.

### Loading and fallbacks

- When a model does not fit in free GPU memory while loading, it is loaded on the CPU instead.
- When no model is requested and `default_tts_model` is not installed, the first installed model in `FALLBACK_TTS_MODELS` (`app/constants/models.py`: Chatterbox, Kokoro, Piper) is used. An explicitly requested model never falls back.

## Parameters

| Parameter | Range | Notes |
| --- | --- | --- |
| `voices_id` | — | Cloned or preset voice. Omit it for the engine's default voice. |
| `engine_voice` | short id | One of the engine's built-in voices, e.g. Kokoro `af_heart` / `af_bella` / `bm_george` or an Edge short name. Overrides the voice's own `engine_voice`. |
| `model_key` | — | Resolved in this order: explicit key → the voice's own cloning model (if installed) → `default_tts_model` → the first installed fallback model. |
| `speed`, `pitch` | 0.5–2.0 | Passed to the engine when it supports them, otherwise applied with librosa. |
| `energy` | 0.1–2.0 | Gain, with peak protection. |
| `emotion` | neutral, happy, sad, angry, calm, excited, fearful, confident | A preset multiplier on speed, pitch and energy. Chatterbox handles emotion natively. |
| `style` | default, narration, conversational, lecture, news, storytelling | Adjusts speed and the pause between sentences. |
| `pause_ms` | ≥ 0 | Gap between chunks. You can also write `[pause 800ms]` or `[pause 2s]` in the text. |
| `pronunciations` | `{word: spoken}` | Whole-word replacement before synthesis. |
| `temperature` | 0.1–1.5 | Chatterbox, Chatterbox Turbo and Qwen3-TTS only. |
| `seed` | int | Chatterbox, Chatterbox Turbo and Qwen3-TTS only. |
| `post` / `preset` | — | Clean-up steps. The default is trim silence + normalize. `{}` means raw output. See [audio-engine.md](audio-engine.md). |
| `cache` | bool | Return an identical earlier generation instead of generating again (see above). |

## Sentence-level work

- `generate_sentences(text)` creates one audio per sentence plus a joined result.
- `regenerate_sentence(audios_ids, index)` produces a new take of one sentence and rebuilds the joined result.
- `regenerate(audios_id, seed)` repeats any generation with the same settings.

## Engines

| Backend | Install | Runs | Native params |
| --- | --- | --- | --- |
| Piper | `uv sync --extra piper`, then install the voice on the Models page | local CPU/GPU | speed |
| Kokoro 82M | `--extra kokoro`, then install it on the Models page (weights download on first load) | local, fine on CPU | speed; built-in voices via `engine_voice` (default `af_heart`) |
| Chatterbox | `--extra chatterbox` | local, GPU recommended | emotion, temperature, seed; cloning, or its built-in voice without a cloned voice |
| Chatterbox Turbo | `--extra chatterbox` (same package) | local, GPU recommended, faster | temperature, seed; cloning from a sample longer than 5 s, or its built-in voice |
| Qwen3-TTS 0.6B | install it on the Models page (from source; it sets up its own environment, see below) | local, helper process | temperature, seed; cloning, or 9 built-in voices via `engine_voice` (default `ryan`); 10 languages |
| Emotional (gTTS) | base | **online** (Google), opt-in | — |
| Edge neural | base | **online** (Microsoft), opt-in | speed, pitch; preset voices via `engine_voice` |

Online engines raise `ModelError` unless **Settings → Allow online engines** is on.

Qwen3-TTS needs a different `transformers` than Chatterbox, so it cannot share VoxLabs' environment. Installing it downloads its weights and sets up `data/engines/qwen3-tts` with uv (`ENGINE_ENVIRONMENTS` in `app/constants/models.py`). Its backend runs `app/utils/engine_workers/qwen3_worker.py` with that environment's Python and exchanges one JSON message per line with it. A built app bundles uv and the worker script; uv fetches a Python of the same version for the environment. Qwen3-TTS is two 0.6B models: Base clones from the speaker embedding of the voice's first sample (no transcript needed), and CustomVoice (`custom_voice/`) speaks its built-in voices (`ryan`, `aiden`, `vivian`, `serena`, `uncle_fu`, `dylan`, `eric`, `ono_anna`, `sohee`). Each loads the first time it is needed. Both use the same speech tokenizer, which is downloaded once and hard-linked.

## Labelling

Every generated audio has `ai_generated = true`. Its file carries the comment tag "AI-generated by VoxLabs", and `params` records the text, voice, model and settings used.

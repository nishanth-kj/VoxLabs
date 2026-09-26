---
name: audio-enhancement
description: Workflow and rules for VoxLabs DSP clean-up steps, enhancement presets and loudness.
---

# Audio enhancement

## Purpose

Clean up generated or recorded speech with configurable DSP steps and presets. The original is always kept.

## Workflow

1. `audio_service.resolve_steps(steps, preset)` merges a preset from `ENHANCE_PRESETS` with explicit steps. `{"step": None}` disables a step. Unknown names raise `ValidationError`.
2. `audio_service.process_array(y, sr, steps)` runs steps in `PROCESS_STEPS` order: trim_silence, denoise, eq, compress, deess, normalize, limit, loudness.
3. `audio_service.process(audios_id, steps, preset)` writes a new processed file and row. TTS and script rendering call `process_array` directly.

## Important rules

- Every step is a method `_<step>(self, y, sr, **options)` on `AudioService` that returns float32. Keep them pure.
- Use the primitives in `app/utils/audio.py` (biquads, loudness, trim). Don't pull in new DSP libraries without a real need.
- Presets live in `app/constants/audio.py` as data only.
- Loudness targets use `au.loudness_lufs()` (K-weighted, gated), and are always followed by the limiter.

## References

- `app/services/audio_service.py`
- `app/utils/audio.py`
- `app/constants/audio.py`
- `docs/audio-engine.md`

## Testing

`tests/test_audio_service.py`:
- `test_every_enhancement_step_runs`
- `test_process_is_non_destructive` (checks that Podcast reaches about −16 LUFS)
- `test_steps_can_be_disabled`

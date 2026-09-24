---
name: tts
description: Workflow and rules for VoxLabs text-to-speech generation, parameters and post-processing.
---

# Text to speech

## Purpose

Generate labelled speech audio from text with a chosen voice, model and speaking parameters.

## Workflow

`tts_service.generate(text, voices_id, model_key, **params)` runs these steps:

1. Validate text and parameters (`Validation` in `app/utils/validation.py`). The input is one `TTSRequest` for the UI, the API and MCP.
2. Apply pronunciations.
3. Resolve the voice with `voice_service.voice_ref()` (enforces consent).
4. Resolve the model with `model_service.resolve_speech_model()`: explicit → the voice's installed cloning model → default.
5. Load the backend with `model_service.backend_for()`.
6. Split text into chunks of ≤ 400 chars, honouring `[pause N]` tags, and synthesize each chunk.
7. Apply emotion and style presets, then DSP prosody for anything the engine can't do natively (`backend.native_params`).
8. For profile-only voices on engines that can't clone, pitch-match to the speaker.
9. Save the original WAV, run `audio_service.process_array()` with the post steps, and register the audio with `ai_generated=True`.

Variants: `generate_async`, `preview`, `regenerate(audios_id, seed)`, `generate_sentences`, `regenerate_sentence`, `combine`.

## Important rules

- Always set `ai_generated=True` and save with `ai_generated=True` so the file gets the metadata tag.
- Keep the raw output as `original_path`. Clean-up writes a separate file.
- Online engines must stay behind `allow_online_models`. `ModelService` enforces this; don't bypass it.
- Put new parameters in `SynthesisRequest` (`app/utils/model.py`) and validate them in `synthesize()`.
- Record every parameter in `params` so `regenerate()` can reproduce a generation.

## References

- `app/services/tts_service.py`
- `app/utils/model.py`
- `app/constants/audio.py` (EMOTIONS, STYLE_PRESETS, DEFAULT_TTS_POST)
- `app/ui/pages/generate_page.py`
- `docs/tts.md`

## Testing

`tests/test_tts_service.py` covers:
- sentence splitting and pause tags
- labelling and the kept original
- speed changing duration
- validation errors
- the online opt-in
- regenerate and per-sentence generation
- cloned vs pitch-matched voices

The default model in tests is the offline `fake-tts`.

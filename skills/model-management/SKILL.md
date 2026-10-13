---
name: model-management
description: Workflow and rules for VoxLabs AI model backends, install/load/unload, device selection and adding engines.
---

# Model management

## Purpose

Discover, install, load and select local AI models (TTS, cloning, enhancement, embedding) without a separate manager layer.

## Workflow

- The catalog is `MODEL_CATALOG` in `app/constants/models.py`. `model_service.sync_catalog()` upserts it into `models` at startup, and it also picks up user-added Piper voices in `data/models/<key>/model.onnx`.
- `install()` checks that the Python package is present and tells the user the `uv sync --inexact --extra …` command if it isn't. It then downloads `files` (direct Hugging Face URLs for every local engine) and loads fetch-on-load engines once (Kokoro, Chatterbox, Chatterbox Turbo) so the download is visible. A model with an `environment` (Qwen3-TTS) gets its own Python environment under `data/engines/<name>`, set up with uv by `create_environment()`.
- `load()` checks the model is allowed (online opt-in), picks a device with `pick_device()` (explicit → settings → CUDA if the model fits in free VRAM minus `gpu_memory_reserve_mb` and within `gpu_memory_budget_mb`, after unloading idle GPU models least recently used first → CPU), creates the backend with the `precision` setting and calls `backend.load()`. A model with `vram_mb: 0` never queries the GPU. Each backend says which devices it can use (`available_devices()`): in-process engines ask VoxLabs' torch, `WorkerBackend` engines offer the GPUs the driver reports because their own PyTorch decides. Loaded backends live in `ModelService._loaded`; loads run one at a time under `_load_lock` and never block lookups of loaded models.
- Generation holds a backend with `with model_service.using(key) as backend:` for each engine call, so it cannot be unloaded mid-call (an unload waits for the call; a model unloaded between calls is loaded again). `max_loaded_models` unloads the least recently used idle model before a new one loads. `load_async()` and `preload_default()` warm the model up (`backend.warm_up()`) so the first generation does not pay one-time costs.
- `unload()`, `reload()`, `remove()`, `health()`, `select(model_type, key)`, `resolve_speech_model()` and `backend_for()` cover the rest.

## Adding an engine

1. Add a catalog entry (key, type, backend, size, VRAM, `package`, `extra`, capabilities, and optional `files`).
2. Add a `ModelBackend` subclass in `app/utils/model.py`. Import heavy libraries inside `load()`. Implement `synthesize()` returning `(float32 mono, sr)`. Set `native_params` and `supports_cloning`. If it clones, call `_require_reference(voice)`. If the engine generates several texts at once, set `max_batch` (and `batch_chunk_chars` when shorter chunks batch better) and implement `synthesize_batch()`. Honour `self.precision` (`auto`/`full`/`half`) where the engine supports reduced precision, and free GPU tensors in `unload()`.
3. Register it in `_BACKENDS`. Add the optional dependency in `pyproject.toml`, then run `uv lock`.
4. If its libraries cannot share VoxLabs' versions (check with `uv lock` and by running it), do not add conflicting extras: `uv run` would swap libraries between them. Add an `ENGINE_ENVIRONMENTS` entry instead (pinned requirements, import check, worker script), set the catalog entry's `environment`, subclass `WorkerBackend`, and write a standalone worker in `app/utils/engine_workers/` that never imports `app`.

## Important rules

- Online engines must set `online: True`. They are only usable when `allow_online_models` is on.
- Never import torch or other engine libraries at module import time.
- Device *inspection* belongs in `app/utils/device.py`. Device *policy* belongs in `ModelService`.
- Document license restrictions (for example a non-commercial model license) in the install flow.

## References

- `app/services/model_service.py`
- `app/utils/model.py`
- `app/utils/device.py`
- `app/constants/models.py`
- `app/ui/pages/models_page.py`

## Testing

- Tests register fake backends with `register_backend()` and patch the catalog (see `tests/conftest.py`).
- `tests/test_api.py::test_scripts_and_models` covers load and unload.
- `tests/test_tts_service.py::test_online_models_are_opt_in` covers the online gate.

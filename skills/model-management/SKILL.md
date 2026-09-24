---
name: model-management
description: Workflow and rules for VoxLabs AI model backends, install/load/unload, device selection and adding engines.
---

# Model management

## Purpose

Discover, install, load and select local AI models (TTS, cloning, enhancement, embedding) without a separate manager layer.

## Workflow

- The catalog is `MODEL_CATALOG` in `app/constants/models.py`. `model_service.sync_catalog()` upserts it into `models` at startup, and it also picks up user-added Piper voices in `data/models/<key>/model.onnx`.
- `install()` checks that the Python package is present and tells the user the `uv sync --extra …` command if it isn't. It then downloads `files` (Piper), or loads the model to fetch its weights (XTTS, F5, Chatterbox). XTTS requires `accept_license=True`.
- `load()` checks the model is allowed (online opt-in), picks a device with `pick_device()` (explicit → settings → CUDA if free VRAM ≥ `vram_mb` → CPU), creates the backend and calls `backend.load()`. Loaded backends live in `ModelService._loaded`.
- `unload()`, `reload()`, `remove()`, `health()`, `select(model_type, key)`, `resolve_speech_model()` and `backend_for()` cover the rest.

## Adding an engine

1. Add a catalog entry (key, type, backend, size, VRAM, `package`, `extra`, capabilities, and optional `files`).
2. Add a `ModelBackend` subclass in `app/utils/model.py`. Import heavy libraries inside `load()`. Implement `synthesize()` returning `(float32 mono, sr)`. Set `native_params` and `supports_cloning`. If it clones, call `_require_reference(voice)`.
3. Register it in `_BACKENDS`. Add the optional dependency in `pyproject.toml`, then run `uv lock`.

## Important rules

- Online engines must set `online: True`. They are only usable when `allow_online_models` is on.
- Never import torch or other engine libraries at module import time.
- Device *inspection* belongs in `app/utils/device.py`. Device *policy* belongs in `ModelService`.
- Document license restrictions (e.g. CPML for XTTS) in the install flow.

## References

- `app/services/model_service.py`
- `app/utils/model.py`
- `app/utils/device.py`
- `app/constants/models.py`
- `app/ui/pages/models_page.py`

## Testing

- Tests register fake backends with `register_backend()` and patch the catalog (see `tests/conftest.py`).
- `tests/test_api.py::test_scripts_projects_users_models` covers load and unload.
- `tests/test_tts_service.py::test_online_models_are_opt_in` covers the online gate.

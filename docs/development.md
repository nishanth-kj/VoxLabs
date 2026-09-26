# Development

## Setup

```bash
uv sync                      # Python 3.12–3.13, base + dev dependencies
uv sync --extra piper        # optional engines: piper, xtts, f5, chatterbox (xtts/f5/chatterbox are mutually exclusive)
uv run python -m app.main    # desktop
uv run uvicorn app.api.app:app --reload
```

`uv` is the only package manager. Add dependencies with `uv add <pkg>` (or `uv add --optional <extra> <pkg>`) and commit both `pyproject.toml` and `uv.lock`. FFmpeg on PATH is optional; it enables M4A/AAC import and export.

Useful environment variables:

| Variable | Effect |
|---|---|
| `VOXLABS_DATA_DIR` | Where the database, audio, voices and models live (default `./data`) |
| `VOXLABS_DB_PATH` | Override only the SQLite file |
| `VOXLABS_API_TOKEN` | Require a bearer token on the API |
| `LOG_LEVEL` | Initial log level (the Settings page can change it) |

## Tests

```bash
uv run pytest                       # everything
uv run pytest tests/test_script_service.py -k render
```

- `tests/conftest.py` gives every test its own `VOXLABS_DATA_DIR`. It registers offline fake engines (`fake-tts`, and `fake-clone` which supports cloning) and makes `fake-tts` the default model. No network or model download happens in tests.
- Test services and utils directly. Test API routes with `TestClient(create_app(initialize=False))`.
- UI tests are smoke tests only (`tests/test_ui.py`, pytest-qt, `QT_QPA_PLATFORM=offscreen`).

## Adding a feature

1. Put the logic in the relevant service, or a new one if it is a genuinely new area. Validate input with `Validation` (`app/utils/validation.py`) and raise `AppError` subclasses. Wrap the public method body in `try: ... except Exception as exc: raise service_error(exc, "<service>.<method>")` and log what it did with `logger`.
2. If it touches several rows, wrap them in one `transaction()`.
3. If it is slow, add a `*_async` wrapper that uses `job_service.submit()`.
4. Call it from the UI with `BasePage.run()` / `follow()`. For the API, add a request class in `app/models/request/` and a thin route in `app/api/routes/`: validate path/query values with `Validation`, pass the full request body to the service, and return `ApiResponse(data).success()` (annotated `-> ApiResponse`). Responses are always HTTP 200. If agents should use it too, add a tool in `app/api/mcp/tools.py` that calls the same service through `respond()`.
5. Add tests next to the existing ones.

## Adding a model engine

1. Add a catalog entry to `MODEL_CATALOG` in `app/constants/models.py` with key, type, backend id, size, VRAM, the Python `package` to probe, `extra` and capabilities. Add `files` if weights are downloaded directly.
2. Add a `ModelBackend` subclass to `app/utils/model.py`:
   - import the library inside `load()`
   - implement `synthesize(request, voice) -> (float32 array, sample_rate)`
   - declare `native_params` and `supports_cloning`
3. Register it in `_BACKENDS`.
4. Add an optional dependency group in `pyproject.toml` and run `uv lock`.

The UI picks it up automatically through `ModelService.list_models()`.

## Packaging

`uv run python scripts/build.py` builds a one-folder desktop bundle with PyInstaller into `dist/VoxLabs/`.

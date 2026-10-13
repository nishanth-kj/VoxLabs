# Development

## Setup

```bash
uv sync                      # Python 3.12–3.13, base + dev dependencies
uv sync --extra piper        # optional engines: piper, kokoro, chatterbox (Chatterbox and Chatterbox Turbo); Qwen3-TTS installs from the Models page
uv run python -m app.main    # desktop
uv run uvicorn app.api.app:app --reload
```

`uv` is the only package manager. Add dependencies with `uv add <pkg>` (or `uv add --optional <extra> <pkg>`) and commit both `pyproject.toml` and `uv.lock`. FFmpeg on PATH is optional; it enables M4A/AAC import and export.

Useful environment variables:

| Variable | Effect |
| --- | --- |
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

If the engine's libraries cannot share VoxLabs' versions, do not add a conflicting extra (`uv run` would swap libraries between the forks). Give it its own environment instead, like Qwen3-TTS: an `ENGINE_ENVIRONMENTS` entry (pinned requirements, the module to import as a check, the worker script), `environment` on the catalog entry, a `WorkerBackend` subclass, and a standalone worker in `app/utils/engine_workers/` that never imports `app`. Installing the model sets the environment up in `data/engines/<name>` with uv.

The UI picks it up automatically through `ModelService.list_models()`.

## Benchmarks

```bash
uv run benchmark                                      # every installed local engine
uv run benchmark --engines kokoro-82m --device cpu    # one engine on the CPU
uv run benchmark --switch chatterbox,chatterbox-turbo,qwen3-tts-0.6b,chatterbox
uv run benchmark --dsp                                # post-processing only
uv run benchmark --out results.json                   # also writes results.md
```

Each engine runs in a fresh process on a temporary data folder linked to the installed models, so the numbers include a real cold start and the library is never touched. See [performance.md](performance.md) for the scenarios, the measured results and the performance settings.

## Packaging

Build the desktop app for the operating system you are on:

```bash
uv run build                 # bundle, self-test, portable package and installers
uv run build --fast          # bundle and self-test only: for trying a change in the built app
```

The bundle gets its own environment, `build/venv`, synced to `uv.lock` with the engines listed in `[tool.voxlabs] build-engines` (or `--engines`). A build therefore never changes your development environment: `.venv` keeps whatever it has, such as a CUDA build of torch, instead of being re-synced on every build, and the bundle always holds exactly the locked versions. uv links packages from its cache, so the first build sets `build/venv` up quickly and later builds find nothing to do. PyInstaller then bundles the app, the bundle is started once with `--self-test` (offscreen, throwaway data folder; a crash prints the app's crash report), and the portable package and the installers are made at the same time (each spends its time in its own compressor, so together they take about as long as the slowest). The build prints how long each step took.

| Built on | Output in `dist/` | Installer tool |
| --- | --- | --- |
| Windows | `VoxLabs-Windows-x64.zip` (portable), `-Setup.exe`, `.msi` | Inno Setup 6 (`winget install JRSoftware.InnoSetup`), WiX 5 (`dotnet tool install --global wix --version 5.0.2`) |
| macOS | `VoxLabs-macOS-arm64.dmg`, `.pkg` | `pkgbuild` (Xcode command line tools) |
| Linux | `VoxLabs-Linux-x86_64.tar.gz` (portable), `.deb`, `.rpm` | `dpkg-deb`, `rpmbuild` (`apt install rpm`) |

- **Setup.exe** installs per user without an admin prompt (all users is offered), adds a Start menu entry, an optional desktop icon and an uninstaller.
- **.msi** installs for all users into Program Files (admin), for IT deployment; newer versions upgrade in place.
- **.pkg** installs `VoxLabs.app` into /Applications; **.deb / .rpm** install to `/opt/voxlabs` with a `voxlabs` command, an app-menu entry and an icon.

Options: `--fast` (same as `--no-package`), `--no-installer` (portable package only), `--no-package` (stop at the bundle), `--skip-self-test`, `--package-only` (reuse the bundle already in `dist/`, e.g. to rebuild just the installers), `--require-installers` (fail instead of skipping an installer whose tool is missing; CI uses it). Only one build runs at a time: a second `uv run build` stops with a message instead of breaking the first.

PyInstaller cannot cross-compile, so each OS's files are built on that OS. `.github/workflows/desktop.yml` runs `uv run build --require-installers` on Windows, macOS and Linux, and a `v*` tag publishes every file as a GitHub release. The builds are not code-signed yet, so SmartScreen and Gatekeeper ask for confirmation on first launch.

A built app keeps its data in the user's app-data folder (`%LOCALAPPDATA%\VoxLabs`, `~/Library/Application Support/VoxLabs`, `~/.local/share/VoxLabs`); from source it stays in `./data`. `VOXLABS_DATA_DIR` overrides both. `uv run build` is the `build` command from `[project.scripts]` (it runs `scripts/build.py`); uv installs the project in editable mode so the command exists. Use `uv sync --inexact` when adding extras, so a sync never removes engines you installed.

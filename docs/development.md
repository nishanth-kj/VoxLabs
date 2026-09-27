# Development

## Setup

```bash
uv sync                      # Python 3.12–3.13, base + dev dependencies
uv sync --extra piper        # optional engines: piper, kokoro, xtts, f5, chatterbox (xtts/f5/chatterbox are mutually exclusive)
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

The UI picks it up automatically through `ModelService.list_models()`.

## Packaging

Build the desktop app for the operating system you are on:

```bash
uv sync --inexact            # add --extra piper --extra kokoro to bundle those engines
uv run build                 # bundle, self-test, portable package and installers
```

It bundles the app with PyInstaller, starts the bundle once with `--self-test` (offscreen, throwaway data folder; a crash prints the app's crash report), then makes the portable package and the installers:

| Built on | Output in `dist/` | Installer tool |
| --- | --- | --- |
| Windows | `VoxLabs-Windows-x64.zip` (portable), `-Setup.exe`, `.msi` | Inno Setup 6 (`winget install JRSoftware.InnoSetup`), WiX 5 (`dotnet tool install --global wix --version 5.0.2`) |
| macOS | `VoxLabs-macOS-arm64.dmg`, `.pkg` | `pkgbuild` (Xcode command line tools) |
| Linux | `VoxLabs-Linux-x86_64.tar.gz` (portable), `.deb`, `.rpm` | `dpkg-deb`, `rpmbuild` (`apt install rpm`) |

- **Setup.exe** installs per user without an admin prompt (all users is offered), adds a Start menu entry, an optional desktop icon and an uninstaller.
- **.msi** installs for all users into Program Files (admin), for IT deployment; newer versions upgrade in place.
- **.pkg** installs `VoxLabs.app` into /Applications; **.deb / .rpm** install to `/opt/voxlabs` with a `voxlabs` command, an app-menu entry and an icon.

Options: `--no-installer` (portable package only), `--no-package` (stop at the bundle), `--skip-self-test`, `--package-only` (reuse the bundle already in `dist/`, e.g. to rebuild just the installers), `--require-installers` (fail instead of skipping an installer whose tool is missing; CI uses it). Only one build runs at a time: a second `uv run build` stops with a message instead of breaking the first.

PyInstaller cannot cross-compile, so each OS's files are built on that OS. `.github/workflows/desktop.yml` runs `uv run build --require-installers` on Windows, macOS and Linux, and a `v*` tag publishes every file as a GitHub release. The builds are not code-signed yet, so SmartScreen and Gatekeeper ask for confirmation on first launch.

A built app keeps its data in the user's app-data folder (`%LOCALAPPDATA%\VoxLabs`, `~/Library/Application Support/VoxLabs`, `~/.local/share/VoxLabs`); from source it stays in `./data`. `VOXLABS_DATA_DIR` overrides both. `uv run build` is the `build` command from `[project.scripts]` (it runs `scripts/build.py`); uv installs the project in editable mode so the command exists. Use `uv sync --inexact` when adding extras, so a sync never removes engines you installed.

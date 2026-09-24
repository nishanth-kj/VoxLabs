# Architecture

VoxLabs is a single Python package, `app/`, with a small number of layers:

```text
PySide6 UI (app/ui)     REST API + MCP (app/api)   ← optional
          \                     /
           Services (app/services)                 ← all application logic
           /                    \
   Models (app/models)       Utils (app/utils)
           \                    /
          SQLite + files under data/
```

The UI, the REST API and the MCP server import the same module-level service singletons, so a feature has exactly one implementation. For example, the Generate page, `POST /api/tts` and the MCP tool `generate_speech` all call `tts_service.generate(body)` with a `TTSRequest`.

## Packages

| Package | Contents |
| --- | --- |
| `app/main.py` | Desktop entry point: initialize services, create `QApplication` and `MainWindow`, optionally start the embedded API. |
| `app/services/` | One service per area: `user`, `voice`, `clone`, `consent`, `tts`, `script`, `audio`, `project`, `model`, `job`, `system`. Each exposes a singleton (`voice_service`, …). |
| `app/models/` | SQLAlchemy tables, one file per table. Data only; no commits and no workflow code. `models/request/` and `models/response/` hold the API's Pydantic request classes and the `ApiResponse` envelope, one class per file. |
| `app/utils/` | Reusable infrastructure: `database` (engine, sessions, `transaction()`, `serialize()`), `audio` (I/O and DSP primitives), `ffmpeg`, `files` (including `save_upload`), `device`, `validation` (the `Validation` class: input checks and JSON-correct response data), `model` (AI engine backends), `hashing`, `time`, `logger`. |
| `app/constants/` | Fixed values, one class per file: `base_enum`, `status`, `consent_status`, `response_status`, `error_code`, `error_message`, `project_type`, `audio_source`, `model_type`, `model_backend`, plus value modules `audio` (formats, presets, limits), `jobs` and `models` (catalog). |
| `app/exceptions/` | `AppError` and its subclasses. Each declares an `ErrorCode` and `ErrorMessage` and carries a specific message plus an optional field. `service_error()` logs a failure once and turns unexpected exceptions into `InternalError`. |
| `app/api/` | FastAPI app (`app.py`), thin routers in `routes/`, and the MCP server in `mcp/` (tools in `mcp/tools.py`, served over streamable HTTP at `/mcp` and over stdio with `--stdio`). Every REST response is HTTP 200 with `ApiResponse`. |
| `app/ui/` | `main_window.py`, ten pages, shared widgets (title bar, nav bar, command palette, player, waveform, timeline, selectors, job status), `app_menu.py` (every command), `theme.py` (dark/light colors and the stylesheet) and `icons.py` (line icons). |

## How a request flows

Here is what happens when you click **Generate** on the Generate page:

1. `GeneratePage.generate()` builds a `TTSRequest` and calls `tts_service.generate_async(body)`.
2. `JobService.submit()` records a `jobs` row (`status = Pending`) and runs the work on a thread pool.
3. `TTSService.generate()` validates the input, resolves the voice (`VoiceService.voice_ref`, which checks consent), resolves the model (`ModelService.resolve_speech_model`) and loads the backend (`ModelService.backend_for`). It then synthesizes chunk by chunk, applies prosody, saves the original WAV, runs `AudioService.process_array`, and registers an `audios` row in one transaction.
4. The job's progress and completion are written to the database and pushed to listeners. `JobBridge` turns those into a Qt signal, and `BasePage.follow()` updates the progress bar and calls back on the UI thread.

The API route `POST /api/tts` validates a `TTSRequest` and passes the whole body to the same `tts_service.generate(body)`. With `background: true` it calls `generate_async(body)` instead and returns the job, as `ApiResponse(data).success()`.

## Errors and logging

- Every public service method is wrapped in `try: ... except Exception as exc: raise service_error(exc, "<service>.<method>")`. `AppError`s pass through (logged once as warnings). Anything else is logged with its traceback and raised as `InternalError`, so callers never see raw library exceptions. Helpers that only take a caller's `session` are not wrapped.
- Routes and pages contain no error handling of their own. The API's exception handlers build the error envelope, and `BasePage.run()` / `follow()` show `exc.message` in a dialog, which is also logged.
- `app/utils/logger.py` is the one logger (`voxlabs`). It writes to stderr, a memory buffer for **Settings → Logs** and `data/logs/voxlabs.log` in the desktop app. It never logs audio content, file bytes or credentials. stdout stays free for the MCP stdio transport.

## Desktop UI

The window follows the Electron / VS Code layout:

- **Title bar** (`widgets/title_bar.py`): the VoxLabs logo, the full menu bar, a command center in the middle that opens the command palette, and the window buttons. The window is frameless and moves and resizes natively, so Windows snapping still works. **Settings → Appearance → Use the system title bar** switches back to a normal frame; the same menus then sit in a regular menu bar.
- **Menus** (`app_menu.py`): File, Edit, View, Voice, Audio, Script, Tools and Help hold every command in the app. A page command navigates to its page and calls the page's own method, so a menu item, a palette entry and a page button all do the same thing. Shortcuts that only apply inside a page (the editor's Ctrl+X, Space, …) are shown as hints and handled by the page, so text boxes keep their own editing keys. The Edit menu acts on the focused text box, otherwise on the audio editor.
- **Command palette** (`widgets/command_palette.py`, Ctrl+Shift+P or F1): searches every menu command.
- **Sidebar** (`widgets/nav_bar.py`): icon + label navigation in sections, collapsible with Ctrl+B.
- **Status bar**: the open project, the REST API / MCP state (click to start or stop it) and background jobs.
- **Theme** (`theme.py`): dark, light or match the system (**View → Theme**). Colors live in `ThemeColors`; widgets that paint themselves (waveform) and icons read `theme.current()`, and `MainWindow.refresh_icons()` re-renders icons after a switch. Use object names such as `Primary`, `Tile`, `Hint` and `Banner` instead of inline colors.

## Background work

- **`JobService`** handles long operations: cloning, TTS, script rendering, model installs and loads, and heavy processing. It keeps a record in the `jobs` table and supports cooperative cancellation (`JobContext.progress()` raises `JobCancelled` once cancel is requested). Jobs left running when the app closes are marked Failed on the next start.
- **`run_async()` / `BasePage.run()`** handle short calls such as listing, analysis and file decoding. They run on `QThreadPool` without a job record.

## Engines

`app/utils/model.py` defines `ModelBackend` (`load`, `unload`, `synthesize`) and one class per engine. Imports of heavy libraries happen inside `load()`, so a missing optional extra only disables that engine. `ModelService` owns the policy: which model to use, which device, when to load, and whether online engines are allowed.

## Settings

`SystemService` stores a small JSON file (`data/settings.json`) covering devices, defaults, GPU, API and logging. There is no configuration framework.

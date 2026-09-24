# Architecture

VoxLabs is a single Python package, `app/`, with a small number of layers:

```text
PySide6 UI (app/ui)          REST API (app/api)   ← optional
          \                     /
           Services (app/services)                 ← all application logic
           /                    \
   Models (app/models)       Utils (app/utils)
           \                    /
          SQLite + files under data/
```

The UI and the API import the same module-level service singletons, so a feature has exactly one implementation. For example, the Generate page and `POST /api/tts` both call `tts_service.generate()`.

## Packages

| Package | Contents |
|---|---|
| `app/main.py` | Desktop entry point: initialize services, create `QApplication` and `MainWindow`, optionally start the embedded API. |
| `app/services/` | One service per area: `user`, `voice`, `clone`, `consent`, `tts`, `script`, `audio`, `project`, `model`, `job`, `system`. Each exposes a singleton (`voice_service`, …). |
| `app/models/` | SQLAlchemy tables, one file per table. Data only; no commits and no workflow code. `models/request/` and `models/response/` hold the API's Pydantic request classes and the `ApiResponse` envelope, one class per file. |
| `app/utils/` | Reusable infrastructure: `database` (engine, sessions, `transaction()`, `serialize()`), `audio` (I/O and DSP primitives), `ffmpeg`, `files`, `device`, `validation`, `model` (AI engine backends), `hashing`, `time`, `logger`. |
| `app/constants/` | Fixed values, one class per file: `base_enum`, `status`, `consent_status`, `response_status`, `project_type`, `audio_source`, `model_type`, `model_backend`, plus value modules `audio` (formats, presets, limits), `jobs` and `models` (catalog). |
| `app/exceptions/` | `AppError` and its subclasses (message + optional field). |
| `app/api/` | FastAPI app (`app.py`) and thin routers in `routes/`. Every response is HTTP 200 with `ApiResponse`. |
| `app/ui/` | `main_window.py`, ten pages and shared widgets (player, waveform, timeline, selectors, job status). |

## How a request flows

Here is what happens when you click **Generate** on the Generate page:

1. `GeneratePage.generate()` calls `tts_service.generate_async(text, **params)`.
2. `JobService.submit()` records a `jobs` row (`status = Pending`) and runs the work on a thread pool.
3. `TTSService.generate()` validates the input, resolves the voice (`VoiceService.voice_ref`, which checks consent), resolves the model (`ModelService.resolve_speech_model`) and loads the backend (`ModelService.backend_for`). It then synthesizes chunk by chunk, applies prosody, saves the original WAV, runs `AudioService.process_array`, and registers an `audios` row in one transaction.
4. The job's progress and completion are written to the database and pushed to listeners. `JobBridge` turns those into a Qt signal, and `BasePage.follow()` updates the progress bar and calls back on the UI thread.

The API route `POST /api/tts` validates a `TTSRequest` and calls the same `tts_service.generate()` directly. With `background: true` it calls `generate_async()` instead and returns the job, wrapped in `ApiResponse.success()`.

## Background work

- **`JobService`** handles long operations: cloning, TTS, script rendering, model installs and loads, and heavy processing. It keeps a record in the `jobs` table and supports cooperative cancellation (`JobContext.progress()` raises `JobCancelled` once cancel is requested). Jobs left running when the app closes are marked Failed on the next start.
- **`run_async()` / `BasePage.run()`** handle short calls such as listing, analysis and file decoding. They run on `QThreadPool` without a job record.

## Engines

`app/utils/model.py` defines `ModelBackend` (`load`, `unload`, `synthesize`) and one class per engine. Imports of heavy libraries happen inside `load()`, so a missing optional extra only disables that engine. `ModelService` owns the policy: which model to use, which device, when to load, and whether online engines are allowed.

## Settings

`SystemService` stores a small JSON file (`data/settings.json`) covering devices, defaults, GPU, API and logging. There is no configuration framework.

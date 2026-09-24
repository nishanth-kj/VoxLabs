# AGENTS.md

Guidance for AI coding agents working in the VoxLabs repository.

## What VoxLabs is

- VoxLabs is a Python desktop application.
- PySide6 is the UI.
- FastAPI is optional REST API support, and `app/api/mcp/` serves the same services as MCP tools (HTTP at `/mcp`, stdio with `--stdio`).
- Services contain application logic.
- Models represent data.
- Utils contain reusable technical infrastructure.
- SQLite is the default database.
- uv manages the Python project.
- There is no web application. `site/` is only the static Next.js **landing page** that links to the desktop download; it is not a product UI and must not grow app features.

Its features are voice cloning (with recorded consent), TTS, script/lesson-to-audio, a non-destructive audio editor, enhancement, projects and takes, local model management, and background jobs.

## Layers

```text
PySide6 UI (app/ui)      REST API + MCP (app/api)
          \                 /
           Services (app/services)      ← all application logic, transactions
           /                \
   Models (app/models)    Utils (app/utils)
           \                /
              SQLite (data/database/voxlabs.db)
```

- The UI, the API and the MCP tools call the **same** service singletons (`from app.services.tts_service import tts_service`). There is exactly one implementation of each feature.
- Never go UI → database, UI → AI model, API → database or API → AI model directly.
- API routes validate path/query values with `Validation` (`app/utils/validation.py`), pass the **full request body** to the service, and `return ApiResponse(data).success()`. Never write `ApiResponse(data=...)`. Routes are annotated `-> ApiResponse` (a `JSONResponse` subclass) and contain no try/except. Error handlers return `ApiResponse(error=exc).error()`.
- Every API response is **HTTP 200**, and the envelope is `{"status": 1|0, "data": ..., "error": null|{...}}`. The error object is exactly `{"error_code", "error_message", "field"}`: `field` maps field names to the specific message. Codes and texts are predefined in the `ErrorCode` and `ErrorMessage` BaseEnums (`app/constants/error_code.py`, `error_message.py`), and each exception class declares its pair.
- MCP tools (`app/api/mcp/tools.py`) take the same request classes and return the same envelope through `respond()`. Voice cloning is not exposed over MCP.
- Each CRUD resource has **one** `POST /api/<resource>` save endpoint: no id → create, id → update, id + `status: Status.DELETED.code` → delete. The dispatch lives in the service's `save()` method.
- Request bodies are Pydantic classes in `app/models/request/`, including multipart forms (`CloneRequest`, `AudioImportRequest` with `Annotated[..., Form()]`). Response classes live in `app/models/response/`. One class per file.
- Do not add repositories, controllers, managers, use-cases, DI frameworks or extra service layers.

## Commands

```bash
uv sync                               # install (add --extra piper / xtts / f5 / chatterbox for engines)
uv run python -m app.main             # desktop app
uv run python -m app.api.app          # REST API + MCP over HTTP (binds 127.0.0.1)
uv run python -m app.api.app --stdio  # the same, plus MCP over stdin/stdout
uv run pytest                         # tests (Qt tests run with QT_QPA_PLATFORM=offscreen)
```

## Conventions

- **Database** (`app/utils/database.py`). Every model declares its own `<table>_id` integer primary key, `status`, `created_at` and `updated_at` columns explicitly in its model file. `Base` is a plain `DeclarativeBase`. Tables are plural (`voices`, `voice_samples`, …).
- **Status.** Constants are `BaseEnum` classes (`app/constants/base_enum.py`) whose members are `(code, value)`, e.g. `Status.IN_PROGRESS.code == 4` and `.value == "InProgress"`. Every table's `status` column is `Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, …)`, and code always reads, writes and queries it with `.code` (`voice.status = Status.INACTIVE.code`, `Audio.status != Status.DELETED.code`). A table that needs its own numbered state gets a separate `<name>_status` column with its own BaseEnum, e.g. `voices.consent_status` → `ConsentStatus`. Never scatter raw status numbers.
- **Transactions.** Services own them with `with transaction() as session:`. Models never commit. Helpers that take a `session` (e.g. `audio_service.register`, `voice_service.create_in`, `consent_service.record`) run inside the caller's transaction.
- **Errors.** Services raise `AppError` subclasses from `app/exceptions` with a specific message and optional `field`. Each class maps to an `ErrorCode`/`ErrorMessage` pair. Every public service method wraps its body in `try: ... except Exception as exc: raise service_error(exc, "<service>.<method>")`, which logs once and turns unexpected exceptions into `InternalError`. The UI shows `exc.message`; the API returns the error object. Stack traces are only logged.
- **Services take request bodies.** Operations exposed by the API take the request class (`tts_service.generate(body: TTSRequest)`, `user_service.save(body: UserRequest)`, `audio_service.process(body: AudioProcessRequest)`); the UI builds the same classes. Upload handling (`save_upload`) and its cleanup live in the service (`clone_service.clone_upload`, `audio_service.import_upload`, `voice_service.attach_upload`).
- **Logging.** Use `from app.utils.logger import logger` everywhere; it writes to stderr (stdout is reserved for MCP stdio), the Settings log view and `data/logs/`. Never log audio content, file bytes or credentials.
- **Long work.** Clone, TTS, render, model install/load and heavy processing go through `job_service.submit()` (thread pool). The UI follows jobs via `BasePage.follow()` and runs short calls with `BasePage.run()`. Never block the Qt thread.
- **Models / engines.** All engine code lives in `app/utils/model.py` behind `ModelBackend`. Heavy libraries are imported lazily inside `load()`. Selection and device policy live in `ModelService`. New engines go in `MODEL_CATALOG` (`app/constants/models.py`) plus a backend class.
- **Files.** Everything goes under `data/` (`app/utils/files.py`, override with `VOXLABS_DATA_DIR`). Only paths are stored in the database.
- **Constants** hold fixed values only, never logic.

## Landing site (`site/`)

- Next.js / TypeScript marketing page deployed to GitHub Pages (`.github/workflows/deploy-nextjs.yml`).
- Commands (from `site/`): `npm install`, `npm run dev`, `npm run build`, `npm run lint`, `npm run test`.
- Keep download/GitHub URLs in `site/lib/links.ts`, and use the existing shadcn/Radix primitives in `site/components/`.
- Never add a web Studio, TTS or cloning to it. The product is the desktop app.

## Safety guarantees (do not weaken without explicit user instruction)

- Voice cloning requires explicit, attributed consent (`ConsentService.validate`), checked before any work. There is no bypass flag.
- Processing is local-first. Online engines (gTTS, Edge) are off unless `allow_online_models` is enabled, and are labelled "online".
- Generated audio is flagged `ai_generated` in the database and tagged "AI-generated by VoxLabs" in file metadata.
- Revoking a voice deletes its samples and profile immediately. Deleting removes everything. Both must stay simple and complete.
- The API binds to 127.0.0.1 by default. Exposing it on another host requires an API token.

## Docs map

- `docs/architecture.md`: layers, packages, background work
- `docs/database.md`: tables, naming, status, transactions
- `docs/audio-engine.md`: AudioService, DSP pipeline, editor ops
- `docs/voice-cloning.md`, `docs/tts.md`, `docs/script-to-audio.md`: feature workflows
- `docs/rest-api.md`: endpoints and the response envelope
- `docs/development.md`: setup, testing, adding engines
- `skills/`: task-oriented workflows for agents

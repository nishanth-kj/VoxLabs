# REST API

The API is optional. It exposes the same services as the desktop app to scripts, other programs and AI agents (through MCP, see below), and it is not a web UI.

```bash
uv run python -m app.api.app                   # REST + MCP over HTTP on 127.0.0.1:8942, docs at /docs
uv run python -m app.api.app --stdio           # the same, plus MCP over stdin/stdout
uv run uvicorn app.api.app:app --reload        # development (127.0.0.1:8000)
```

It can also run inside the desktop app (**Settings → REST API**; the default port is 8942). The MCP endpoint `/mcp` is included wherever the API runs.

## Security

- It binds to `127.0.0.1` by default.
- To expose it on another host, set a token first with `VOXLABS_API_TOKEN` or **Settings → API token**. The desktop refuses to start a non-loopback server without one.
- With a token set, every route except `/api/health` and the docs needs `Authorization: Bearer <token>`.

## Conventions

- **Always HTTP 200.** Every response, errors included, is HTTP 200. Routes return `ApiResponse(data).success()` (`app/models/response/api_response.py`, a `JSONResponse` subclass, so routes are annotated `-> ApiResponse`); the error handlers return `ApiResponse(error=exc).error()`. Clients check `status` (from `ResponseStatus`: 1 = Success, 0 = Error):

  ```json
  { "status": 1, "data": { ... }, "error": null }
  { "status": 0, "data": null, "error": {
      "error_code": 404, "error_message": "The requested item was not found.",
      "field": { "voices_id": "Voice 42 not found" } } }
  ```

  The `error` object:

  | Key | Contents |
  | --- | --- |
  | `error_code` | `ErrorCode.code`, which follows HTTP meanings |
  | `error_message` | `ErrorMessage.value`, the predefined text |
  | `field` | an object mapping field name → the specific message (validation lists every invalid field) |

  Stack traces are never returned.

  | error_code | Raised as |
  | --- | --- |
  | 400 | `AppError`, `AudioError`, `ProjectError` |
  | 401 | `AuthError` (missing or wrong API token) |
  | 403 | `ConsentError` |
  | 404 | `NotFoundError`, unknown route |
  | 409 | `VoiceError`, `JobError` |
  | 422 | `ValidationError`, invalid request body |
  | 500 | `InternalError`, unexpected exceptions |
  | 503 | `ModelError` (model not installed, online engines disabled, load failure) |

- **Route shape.** A route validates its inputs with `Validation` (`app/utils/validation.py`), passes the **full request body** to the service, and returns the result. Routes contain no try/except: services catch, log and convert errors (`service_error()`), and the global handlers build the error envelope.

  ```python
  @router.get("")
  def list_audio(projects_id: int | None = None, limit: int = 100) -> ApiResponse:
      projects_id = Validation.optional_id(projects_id, "projects_id")
      limit = Validation.limit(limit)
      data = audio_service.list_audios(projects_id, limit)
      return ApiResponse(data).success()


  @router.post("/process")
  def process_audio(body: AudioProcessRequest) -> ApiResponse:
      data = {"job": audio_service.process_async(body)} if body.background else audio_service.process(body)
      return ApiResponse(data).success()
  ```

  `ApiResponse` passes the data through `Validation.response_data()`, so values always go out as JSON types (dates as ISO text, paths as text, integer status codes, no NaN).
- **One save endpoint per resource.** `POST /api/<resource>` creates, updates or deletes, depending on the body:

  | Body | Action |
  | --- | --- |
  | no `<table>_id` | create |
  | `<table>_id` | update the given fields |
  | `<table>_id` + `"status": 8` (`Status.DELETED.code`) | delete |

  The route calls the service's `save(body)` method, which does the dispatch.
- **Request and response classes.** Request bodies are Pydantic classes in `app/models/request/`, one class per file (`UserRequest`, `VoiceRequest`, `TTSRequest`, …). Multipart forms are request classes too (`CloneRequest`, `AudioImportRequest`, declared as `Annotated[CloneRequest, Form()]`), including their `UploadFile` fields.
- **Status labels.** `status` values are integer codes, and a readable label is included next to them, e.g. `"status": 5, "status_label": "Completed"`.

## Endpoints

| Method & path | Request class | Service call |
| --- | --- | --- |
| `GET /api/health`, `GET /api/presets` | — | `system_service.health()` / `presets()` |
| `GET /api/users`, `GET /api/users/{id}` | — | `user_service.list_users()` / `get_user()` |
| `POST /api/users` | `UserRequest` | `user_service.save(body)` |
| `GET /api/voices`, `GET /api/voices/{id}` | — | `voice_service.list_voices()` / `get()` |
| `POST /api/voices` | `VoiceRequest` | `voice_service.save(body)` (creates *preset* voices) |
| `POST /api/voices/clone` | `CloneRequest` (multipart form) | `clone_service.clone_upload(body)` |
| `POST /api/voices/analyze` | multipart `sample` | `clone_service.analyze_upload()` |
| `POST /api/voices/{id}/revoke`, `GET /api/voices/{id}/export` | — | `voice_service.revoke()` / `export_metadata()` |
| `POST /api/voices/{id}/samples`, `POST /api/voices/samples/{sample_id}/remove` | multipart `audio` | `attach_upload()` / `remove_sample()` |
| `POST /api/tts` | `TTSRequest` | `tts_service.generate(body)` / `generate_async(body)` |
| `POST /api/tts/regenerate` | `RegenerateRequest` | `tts_service.regenerate(body)` |
| `GET /api/scripts`, `GET /api/scripts/{id}` | — | `script_service.list_scripts()` / `get()` |
| `POST /api/scripts` | `ScriptRequest` | `script_service.save(body)` |
| `POST /api/scripts/{id}/generate` | `GenerateScriptRequest` | `script_service.generate(id, body)` / `generate_async(id, body)` (default `background: true`) |
| `POST /api/scripts/sections` | `SectionRequest` | `script_service.update_section(body)` |
| `POST /api/scripts/sections/{id}/generate`, `POST /api/scripts/takes/{id}/select` | — | section and take operations |
| `GET /api/audio`, `GET /api/audio/{id}`, `GET /api/audio/{id}/file` | — | `audio_service.list_audios()` / `get()` / file download |
| `POST /api/audio/import` | `AudioImportRequest` (multipart `file`, `projects_id`) | `audio_service.import_upload(body)` |
| `POST /api/audio/process` | `AudioProcessRequest` | `audio_service.process(body)`: steps/preset, or an `ops` edit list |
| `POST /api/audio/export` | `AudioExportRequest` | `audio_service.export(body)`, returns the file |
| `GET /api/projects`, `GET /api/projects/{id}` | — | `project_service.list_projects()` / `open_project()` |
| `POST /api/projects` | `ProjectRequest` | `project_service.save(body)` |
| `POST /api/projects/{id}/duplicate` | — | `project_service.duplicate_project()` |
| `GET /api/models`, `GET /api/models/{id}`, `POST …/load`, `…/unload`, `…/install`, `GET …/health` | — | `model_service` (id is the numeric `models_id` or the key) |
| `GET /api/jobs`, `GET /api/jobs/{id}`, `POST /api/jobs/{id}/cancel` | — | `job_service` |

## MCP server

The same services are available to AI agents as MCP (Model Context Protocol) tools, from `app/api/mcp/`:

- **HTTP**: streamable HTTP at `POST /mcp` on the API server (same host, port and token as the REST API).
- **stdio**: `uv run python -m app.api.app --stdio` serves MCP on stdin/stdout **and** starts the HTTP server (REST + `/mcp`) in the same process. It stops when the MCP client closes stdin. Logs go to stderr, so stdout carries only MCP messages.

Example client configuration (stdio):

```json
{ "mcpServers": { "voxlabs": {
    "command": "uv",
    "args": ["run", "--directory", "C:/Projects/VoxLabs", "python", "-m", "app.api.app", "--stdio"] } } }
```

Tools take the same request classes as the REST routes (for example `generate_speech(body: TTSRequest)` or `save_script(body: ScriptRequest)`) and return the same `{status, data, error}` envelope. A failed call is an MCP tool error whose text is the error envelope.

| Area | Tools |
| --- | --- |
| System | `health`, `presets` |
| Users | `list_users`, `save_user` |
| Voices | `list_voices`, `get_voice`, `save_voice` |
| Speech | `generate_speech`, `regenerate_speech` |
| Audio | `list_audio`, `get_audio`, `process_audio`, `export_audio` |
| Scripts | `list_scripts`, `get_script`, `save_script`, `update_section`, `generate_script` |
| Projects | `list_projects`, `get_project`, `save_project` |
| Models and jobs | `list_models`, `list_jobs`, `get_job`, `cancel_job` |

Voice cloning is **not** an MCP tool. Consent has to come from the speaker (the desktop app or the REST form), not from an agent.

## Examples

```bash
# Create, update, then delete a user with the same endpoint
curl -s -X POST 127.0.0.1:8000/api/users -H 'Content-Type: application/json' -d '{"name": "Ada"}'
curl -s -X POST 127.0.0.1:8000/api/users -H 'Content-Type: application/json' -d '{"users_id": 1, "email": "ada@example.com"}'
curl -s -X POST 127.0.0.1:8000/api/users -H 'Content-Type: application/json' -d '{"users_id": 1, "status": 8}'

# Speech with the default model
curl -s -X POST 127.0.0.1:8000/api/tts -H 'Content-Type: application/json' \
  -d '{"text": "Hello from VoxLabs.", "emotion": "calm"}'

# Clone a voice (consent fields are mandatory)
curl -s -X POST 127.0.0.1:8000/api/voices/clone \
  -F name="Narrator" -F consent=true -F granted_by="Jane Doe" -F speaker_name="Jane Doe" \
  -F samples=@jane.wav

# Render a script in the background and poll the job
curl -s -X POST 127.0.0.1:8000/api/scripts/1/generate -H 'Content-Type: application/json' -d '{}'
curl -s 127.0.0.1:8000/api/jobs/12
```

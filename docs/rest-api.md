# REST API

The API is optional. It exposes the same services as the desktop app to scripts and other programs, and it is not a web UI.

```bash
uv run uvicorn app.api.app:app                 # 127.0.0.1:8000, interactive docs at /docs
uv run uvicorn app.api.app:app --reload        # development
```

It can also run inside the desktop app (**Settings → REST API**; the default port is 8942).

## Security

- It binds to `127.0.0.1` by default.
- To expose it on another host, set a token first with `VOXLABS_API_TOKEN` or **Settings → API token**. The desktop refuses to start a non-loopback server without one.
- With a token set, every route except `/api/health` and the docs needs `Authorization: Bearer <token>`.

## Conventions

- **Always HTTP 200.** Every response, errors included, is HTTP 200. Routes build it with `ApiResponse(data=...).success()`; the error handlers use `ApiResponse(error=exc).error()` (`app/models/response/api_response.py`). Clients check `status` (from `ResponseStatus`: 1 = Success, 0 = Error):

  ```json
  { "status": 1, "data": { ... }, "error": null }
  { "status": 0, "data": null, "error": {
      "type": "NotFound", "error_code": 404, "error_message": "The requested item was not found.",
      "field": { "voices_id": "Voice 42 not found" }, "detail": "Voice 42 not found" } }
  ```

  The `error` object:

  | Key | Contents |
  |---|---|
  | `type` | `ErrorCode.value`, a stable label |
  | `error_code` | `ErrorCode.code`, which follows HTTP meanings |
  | `error_message` | `ErrorMessage.value`, the predefined text |
  | `field` | an object mapping field name → message (validation lists every invalid field) |
  | `detail` | the specific message from the service |

  Stack traces are never returned.

  | error_code | type | Raised as |
  |---|---|---|
  | 400 | BadRequest | `AppError`, `AudioError`, `ProjectError` |
  | 401 | Unauthorized | `AuthError` (missing or wrong API token) |
  | 403 | ConsentRequired | `ConsentError` |
  | 404 | NotFound | `NotFoundError`, unknown route |
  | 409 | Conflict | `VoiceError`, `JobError` |
  | 422 | ValidationError | `ValidationError`, invalid request body |
  | 500 | InternalServerError | `InternalError`, unexpected exceptions |
  | 503 | ServiceUnavailable | `ModelError` (model not installed, online engines disabled, load failure) |

- **One save endpoint per resource.** `POST /api/<resource>` creates, updates or deletes, depending on the body:

  | Body | Action |
  |---|---|
  | no `<table>_id` | create |
  | `<table>_id` | update the given fields |
  | `<table>_id` + `"status": 8` (`Status.DELETED.code`) | delete |

  The route calls the service's `save()` method, which does the dispatch.
- **Request and response classes.** Request bodies are Pydantic classes in `app/models/request/`, one class per file (`UserRequest`, `VoiceRequest`, `TTSRequest`, …). Routes validate with them, pass the fields to a service and return `ApiResponse(data=...).success()`.
- **Status labels.** `status` values are integer codes, and a readable label is included next to them, e.g. `"status": 5, "status_label": "Completed"`.

## Endpoints

| Method & path | Request class | Service call |
|---|---|---|
| `GET /api/health`, `GET /api/presets` | — | `system_service.health()` / `presets()` |
| `GET /api/users`, `GET /api/users/{id}` | — | `user_service.list_users()` / `get_user()` |
| `POST /api/users` | `UserRequest` | `user_service.save()` |
| `GET /api/voices`, `GET /api/voices/{id}` | — | `voice_service.list_voices()` / `get()` |
| `POST /api/voices` | `VoiceRequest` | `voice_service.save()` (creates *preset* voices) |
| `POST /api/voices/clone` | multipart form | `clone_service.clone()` / `clone_async()` |
| `POST /api/voices/analyze` | multipart `sample` | `clone_service.analyze_sample()` |
| `POST /api/voices/{id}/revoke`, `GET /api/voices/{id}/export` | — | `voice_service.revoke()` / `export_metadata()` |
| `POST /api/voices/{id}/samples`, `POST /api/voices/samples/{sample_id}/remove` | multipart `audio` | `attach_sample()` / `remove_sample()` |
| `POST /api/tts` | `TTSRequest` | `tts_service.generate()` / `generate_async()` |
| `POST /api/tts/regenerate` | `RegenerateRequest` | `tts_service.regenerate()` |
| `GET /api/scripts`, `GET /api/scripts/{id}` | — | `script_service.list_scripts()` / `get()` |
| `POST /api/scripts` | `ScriptRequest` | `script_service.save()` |
| `POST /api/scripts/{id}/generate` | `GenerateScriptRequest` | `script_service.generate()` / `generate_async()` (default `background: true`) |
| `POST /api/scripts/sections` | `SectionRequest` | `script_service.update_section()` |
| `POST /api/scripts/sections/{id}/generate`, `POST /api/scripts/takes/{id}/select` | — | section and take operations |
| `GET /api/audio`, `GET /api/audio/{id}`, `GET /api/audio/{id}/file` | — | `audio_service.list_audios()` / `get()` / file download |
| `POST /api/audio/import` | multipart `file` | `audio_service.import_file()` |
| `POST /api/audio/process` | `AudioProcessRequest` | `process()` with steps/preset, or `render_edits()` with `ops` |
| `POST /api/audio/export` | `AudioExportRequest` | `audio_service.export()`, returns the file |
| `GET /api/projects`, `GET /api/projects/{id}` | — | `project_service.list_projects()` / `open_project()` |
| `POST /api/projects` | `ProjectRequest` | `project_service.save()` |
| `POST /api/projects/{id}/duplicate` | — | `project_service.duplicate_project()` |
| `GET /api/models`, `GET /api/models/{id}`, `POST …/load`, `…/unload`, `…/install`, `GET …/health` | — | `model_service` (id is the numeric `models_id` or the key) |
| `GET /api/jobs`, `GET /api/jobs/{id}`, `POST /api/jobs/{id}/cancel` | — | `job_service` |

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

---
name: development
description: Setup, conventions and the end-to-end workflow for adding or changing a VoxLabs feature.
---

# Development

## Purpose

Make changes that fit VoxLabs' small architecture: PySide6 UI and optional FastAPI, both on top of shared services.

## Setup

```bash
uv sync                       # add --extra piper for a real offline engine
uv run python -m app.main     # desktop
uv run uvicorn app.api.app:app --reload
uv run pytest
```

## Workflow for a feature

1. **Service first.** Add or extend a method in `app/services/<area>_service.py`:
   - validate with `Validation` (`app/utils/validation.py`);
   - raise `AppError` subclasses;
   - wrap multi-row writes in `transaction()`;
   - return plain dicts (`serialize()`);
   - wrap the public method in `try: ... except Exception as exc: raise service_error(exc, "<service>.<method>")` and log with `logger`.
2. **Data.** If you need a new column or table, edit the model file and declare `<table>_id`, `status` (`Integer`, `default=Status.ACTIVE.code`), `created_at` and `updated_at` explicitly. If a table needs its own numbered state, add a `<name>_status` column and a new BaseEnum const.
3. **Slow?** Add a `*_async` wrapper using `job_service.submit(JobType.X, fn, title=…)`. `fn(ctx)` should call `ctx.progress(v)`.
4. **UI.** In the page, call `self.run(fn, on_done)` for quick calls and `self.follow(job, on_done)` for jobs. Never call services that do I/O directly in a slot.
5. **API.** Add a request class in `app/models/request/` (one class per file; multipart forms too) and a thin route: validate path/query values with `Validation`, pass the full request body to the service, `return ApiResponse(data).success()`, annotated `-> ApiResponse`. No try/except in routes. For agents, add a matching tool in `app/api/mcp/tools.py`.
   - Responses are always HTTP 200, and errors propagate to the envelope handler.
   - A CRUD resource gets a single `POST /api/<resource>` backed by the service's `save()`: no id → create, id → update, id + Deleted status → delete.
6. **Tests.** Add service tests, and route tests where useful. Run `uv run pytest`.
7. **Docs.** Update the matching `docs/*.md` and skill file when behaviour changes.

## Important rules

- No repositories, controllers, managers, DI frameworks or extra layers.
- Constants hold values, never logic.
- Never commit anything under `data/`. Do commit `uv.lock`.
- Keep the safety guarantees in `AGENTS.md`.

## References

- `AGENTS.md`
- `docs/architecture.md`
- `docs/database.md`
- `docs/development.md`

## Testing guidance

- The fixtures in `tests/conftest.py` isolate data per test and provide offline engines.
- Keep UI tests to smoke tests (`tests/test_ui.py`). Put logic tests on services.

# Contributing to VoxLabs

Thanks for helping. VoxLabs is a Python desktop app (PySide6) with an optional FastAPI layer, both built on shared services. Please read [AGENTS.md](../AGENTS.md) and [architecture.md](./architecture.md) before making larger changes.

## Code of conduct

Be respectful and constructive. Harassment, discrimination and publishing others' private information are not acceptable. This project clones real people's voices, so contributions must keep its consent, labelling and local-first guarantees intact.

## Getting started

```bash
git clone https://github.com/nishanth-kj/VoxLabs.git
cd VoxLabs
uv sync                      # Python 3.12–3.13
uv run pytest
uv run python -m app.main
```

See [development.md](./development.md) for environment variables, optional engines and packaging.

## Making changes

1. Create a branch: `git checkout -b feature/short-description`.
2. Put logic in `app/services/`. UI pages and API routes only call services.
3. Follow the database conventions in [database.md](./database.md):
   - explicit `<table>_id`, `status`, `created_at` and `updated_at` on every model;
   - `status` stored as an Integer through `Status.X.code`.
4. Keep slow work in background jobs (`job_service.submit`).
5. Add or update tests in `tests/` and run `uv run pytest`.
6. Update the relevant `docs/` page and `skills/` file when behaviour changes.

## Coding style

- Python 3.12, type hints on public functions, 120-character lines.
- Match the surrounding code: small functions, plain dicts across the service boundary, no new frameworks without a clear need.
- Manage dependencies with `uv add` only, and commit `pyproject.toml` and `uv.lock` together.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/), for example `feat: add de-esser step` or `fix: keep takes when editing script body`.

## Pull requests

- Describe what changed and why, and how you tested it.
- Include screenshots for UI changes.
- CI runs `uv sync --frozen` and `uv run pytest` on Ubuntu with an offscreen Qt platform.

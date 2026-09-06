# AGENTS.md

Guidance for AI coding agents working in the VoxLabs repository.

## Project Overview

VoxLabs is an AI voice cloning and TTS platform with three cooperating pieces:

- **`api/`** — FastAPI backend (Python 3.12+, `uv`-managed). Class-based **Routes → Services** architecture: `api/routes/` holds `APIRouter` handlers (`SystemRoutes`, `VoiceRoutes`, `TTSRoutes`), `api/services/` holds the business logic they call into (`SystemService`, `VoiceService`, `TTSService`, `EdgeTTSService`). Audio DSP (time-stretch, pitch-shift, energy) lives in the `EmotionalTTSEngine` and uses `librosa`.
- **`web/`** — Next.js 16 / React 19 / TypeScript frontend ("Studio" UI), Tailwind + shadcn/Radix components, tested with Vitest.
- **`api/desktop/`** — PyQt6 desktop shell.

All API responses follow `{ "status": 1|0, "data": {...}, "error": null|string }`.

## Setup & Common Commands

Backend (from `api/`):
```bash
uv sync
uv run uvicorn main:app --reload --port 8000
```

Frontend (from `web/`):
```bash
npm install
npm run dev      # dev server
npm run build
npm run lint      # eslint
npm run test      # vitest
```

Full stack via Docker: `docker-compose up -d --build` (web on `:3000`, API on `:8000`, docs at `/docs`).

## Conventions

- **Backend**: keep new HTTP handlers thin — request/response glue only in `routes/`, all logic in `services/`. Match the existing standardized JSON envelope for every endpoint.
- **Frontend**: use existing shadcn/Radix primitives in `web/components/` rather than adding new UI libraries; keep API calls behind `web/lib/`.
- Do not commit secrets; use `.env` (see `.env.example`) and never hardcode API URLs — the frontend reads `NEXT_PUBLIC_API_URL`.

## Safety & Ethics (non-negotiable for this project)

VoxLabs clones real people's voices, so agent changes must preserve these product guarantees — do not remove or weaken them without explicit user instruction:

- Voice cloning requires explicit consent; don't add flows that bypass consent capture.
- Processing stays local-first — no silent uploads of user audio/voice data to external/third-party services.
- Generated audio must remain labeled as AI-generated.
- Voice data deletion/revocation must stay simple and complete.

## Docs Map

- [`docs/backend.md`](./docs/backend.md) — API architecture, DSP/emotion presets
- [`docs/api.md`](./docs/api.md) — endpoint reference
- [`docs/frontend.md`](./docs/frontend.md) — Studio UI, state management
- [`docs/setup.md`](./docs/setup.md) — local dev & Docker setup

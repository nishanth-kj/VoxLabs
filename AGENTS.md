# AGENTS.md

Guidance for AI coding agents working in the VoxLabs repository.

## Project Overview

VoxLabs is an AI voice cloning and TTS platform with three cooperating pieces:

- **`api/`** — FastAPI backend (Python 3.12+, `uv`-managed). Class-based **Routes → Services** architecture: `api/routes/` holds `APIRouter` handlers (`SystemRoutes`, `VoiceRoutes`, `TTSRoutes`), `api/services/` holds the business logic they call into (`SystemService`, `VoiceService`, `TTSService`, `EdgeTTSService`). Audio DSP (time-stretch, pitch-shift, energy) lives in the `EmotionalTTSEngine` and uses `librosa`.
- **`desktop/`** — the product UI: a Tauri (Rust) shell wrapping a Next.js 16 / TypeScript frontend, statically exported (`output: "export"`) and bundled into the native app. It calls the FastAPI backend over HTTP; it does not import Python.
- **`site/`** — Next.js 16 / React 19 / TypeScript **landing page**. It tells visitors to download the desktop app. It is not a web Studio.

All API responses follow `{ "status": 1|0, "data": {...}, "error": null|string }`.

## Setup & Common Commands

First-time setup: `npm install` from the repo root. Its `postinstall` (`scripts/bootstrap.mjs`) checks for `uv`, Rust, and FFmpeg, installs whichever is missing, then runs `uv sync` in `api/` and `npm install` in `desktop/`. Re-running it is safe/idempotent. Rust's own dependencies (`desktop/src-tauri/Cargo.toml`) need no separate step — Cargo fetches and builds them automatically on the first `tauri dev`/`tauri build`.

Backend (from `api/`):
```bash
uv sync
uv run uvicorn main:app --reload --port 8000
```

Landing site (from `site/`):
```bash
npm install
npm run dev      # landing page
npm run build
npm run lint      # eslint
npm run test      # vitest
```

Desktop app (from `desktop/`):
```bash
npm install
npm run tauri dev     # native window
npm run dev           # browser-only, at :3010, no Rust build needed
```

Shortcut from the repo root: `npm run dev` (API + browser-only frontend, the default for day-to-day work) or `npm run dev:desktop` (API + native window). See root `package.json`.

Full stack via Docker: `docker-compose up -d --build` (landing site on `:3000`, API on `:8000`).

## Conventions

- **Backend**: keep new HTTP handlers thin — request/response glue only in `routes/`, all logic in `services/`. Match the existing standardized JSON envelope for every endpoint.
- **Desktop app**: the frontend is plain TypeScript/React calling `api.ts` (`desktop/src/lib/api.ts`), which talks to the FastAPI backend over HTTP — never add a Python/PyQt6 GUI back in. Keep `next.config.ts`'s `output: "export"` intact; Tauri bundles the static export, not a Node server.
- **Landing site**: use existing shadcn/Radix primitives in `site/components/` rather than adding new UI libraries. Keep download/GitHub URLs in `site/lib/links.ts`. Do not reintroduce a web Studio — the product is the desktop app.
- Do not commit secrets; use `.env` (see `.env.example`).

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

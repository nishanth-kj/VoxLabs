# VoxLabs Studio (Desktop)

The VoxLabs desktop app: a [Tauri](https://tauri.app) (Rust) shell wrapping a statically-exported Next.js/TypeScript frontend. It is the product UI — see [`../docs/frontend.md`](../docs/frontend.md) and [`../AGENTS.md`](../AGENTS.md) for how this fits with `site/` (the landing page) and `api/` (the FastAPI backend).

## Development

Run the FastAPI backend first (see [`../docs/setup.md`](../docs/setup.md)), then:

```bash
npm install
npm run tauri dev
```

This starts the Next.js dev server on `:3010` and opens it in a native Tauri window. The frontend talks to the backend at `http://127.0.0.1:8000` (override with `NEXT_PUBLIC_API_URL`).

## Building

```bash
npm run tauri build
```

Runs `next build` (static export to `out/`) and bundles it with the Rust shell into a native installer.

## Structure

- `src/app/` — Next.js App Router pages (Dashboard, Voice Library, Clone Voice, Text to Speech)
- `src/lib/api.ts` — typed fetch client for the FastAPI backend
- `src/components/` — shared UI (sidebar, buttons, inputs, sliders)
- `src-tauri/` — the Rust shell and `tauri.conf.json`

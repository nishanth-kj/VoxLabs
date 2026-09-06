# Setup & Deployment Guide

## Prerequisites

- **Node.js**: 20 or higher (npm comes with it)

That's it — Python, Rust, and FFmpeg don't need to be pre-installed. Running `npm install` from the repo root checks for **uv**, **Rust**, and **FFmpeg** and installs whichever is missing (via the official astral.sh/rustup.rs installers, and winget/brew/apt/dnf/pacman for FFmpeg depending on OS), then runs `uv sync` for the Python backend and `npm install` for the desktop app. See [`scripts/bootstrap.mjs`](../scripts/bootstrap.mjs). Re-run `npm install` (or `npm run setup`) any time to check again — it's safe to run repeatedly. If FFmpeg was just installed for the first time, open a new terminal before running anything that needs it.

Once Rust is present, its own dependencies (Tauri, wry, tao, etc. — `desktop/src-tauri/Cargo.toml`) don't need any setup step either: Cargo downloads and compiles them automatically the first time you run `npm run dev:desktop` or `npm run build:desktop`, the same way `npm install` resolves a `package.json`.

## Quick Start (Docker)

The easiest way to run VoxLabs is using Docker Compose.

1.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```
2.  **Access**:
    - Landing site: `http://localhost:3000`
    - API Docs: `http://localhost:8000/docs`

## Local Development

Fastest path: `npm install` from the repo root (see Prerequisites above), then `npm run dev` — this installs everything and starts the backend plus the desktop app's web frontend together.

If you prefer to run services manually:

### 1. Backend (API)

```bash
cd api
# Install dependencies (using uv or pip)
uv sync  # or pip install -r requirements.txt

# Run Server
uv run uvicorn main:app --reload --port 8000
```

### 2. Landing site

```bash
cd site
# Install dependencies
npm install

# Run Development Server
npm run dev
```

Visit `http://localhost:3000` for the download landing page. The product UI is the desktop app, not this site.

### GitHub Pages

The landing site is a static Next.js export. On push to `main`, [`.github/workflows/deploy-nextjs.yml`](../.github/workflows/deploy-nextjs.yml) builds `site/` and deploys it.

1. In the GitHub repo: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Push to `main` (or run the **Deploy Next.js to GitHub Pages** workflow).
3. The site is served at `https://<owner>.github.io/<repo>/` (for this repo, typically `https://nishanth-kj.github.io/VoxLabs/`).

Local production build (no Docker):

```bash
cd site
npm run build
npm run preview
```

### 3. Desktop App (Tauri + Next.js)

```bash
cd desktop
npm install
npm run tauri dev
```

This opens the native window backed by the Next.js frontend (`http://localhost:3010` in dev). It talks to the FastAPI backend, so keep step 1 running alongside it.

To view the same UI in a regular browser instead of the native window, run `npm run dev` (inside `desktop/`) and open `http://localhost:3010` directly — no Rust build required.

**Shortcut:** from the repo root, `npm install && npm run dev` starts the backend and the browser-only frontend together (single Ctrl+C stops both) — this is the default for day-to-day work since it needs no Rust build. Use `npm run dev:desktop` instead when you specifically need the native window. `npm run build:desktop` builds the installer.

## Troubleshooting

- **FFmpeg Error**: If you see errors about "ffmpeg not found" right after `npm install` installed it, open a new terminal — a fresh install isn't on the current terminal's PATH yet. If it still fails, install it manually and confirm it's on PATH.
- **API Connection**: Ensure the backend is running on `localhost:8000`. The frontend expects this default URL.
